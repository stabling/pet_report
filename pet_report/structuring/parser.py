from __future__ import annotations

import re
from collections import OrderedDict

from pet_report.core.config import get_settings
from pet_report.core.trace import new_trace_id
from pet_report.knowledge.references import ReferenceRangeStore
from pet_report.models.schemas import (
    LabItem,
    OcrLine,
    PetProfile,
    ReferenceRange,
    ReportSource,
    Species,
    StructuredReport,
)
from pet_report.structuring.units import convert_value, extract_reference_from_line, normalize_unit


VALUE_PATTERN = re.compile(
    r"(?P<name>[A-Za-z]{2,6}|[\u4e00-\u9fa5]{2,12})\s*[:：]?\s*"
    r"(?P<value>[<>]?-?\d+(?:\.\d+)?)\s*"
    r"(?P<unit>(?:10\^?\d+/L|x10\^?\d+/L|\d{2,4}/L|[munµμ]?[gmol]+/[dL]+|mg/dL|mmol/L|umol/L|µmol/L|μmol/L|g/L|U/L|IU/L))?",
    flags=re.IGNORECASE,
)


def parse_numeric(raw: str) -> float | None:
    raw = raw.strip()
    raw = raw.lstrip("<>")
    try:
        return float(raw)
    except ValueError:
        return None


class ReportStructurer:
    def __init__(self, reference_store: ReferenceRangeStore | None = None) -> None:
        settings = get_settings()
        self.reference_store = reference_store or ReferenceRangeStore(settings.reference_path)

    def structure(
        self,
        lines: list[OcrLine],
        pet_profile: PetProfile,
        report_source: ReportSource,
        trace_id: str | None = None,
    ) -> StructuredReport:
        trace_id = trace_id or new_trace_id()
        lab_items = self._extract_items(lines, pet_profile.species)
        warnings = self._quality_warnings(lines, lab_items)
        return StructuredReport(
            trace_id=trace_id,
            pet_profile=pet_profile,
            report_source=report_source,
            ocr_lines=lines,
            lab_items=lab_items,
            quality_warnings=warnings,
            metadata={"reference_version": self.reference_store.version},
        )

    def _extract_items(self, lines: list[OcrLine], species: Species) -> list[LabItem]:
        found: OrderedDict[str, LabItem] = OrderedDict()
        joined_lines = self._join_lines_for_short_tokens(lines)
        for line, confidence in joined_lines:
            for match in VALUE_PATTERN.finditer(line):
                raw_name = match.group("name")
                code, spec = self.reference_store.canonicalize(raw_name)
                if not code or not spec:
                    continue
                raw_value = match.group("value")
                value = parse_numeric(raw_value)
                raw_unit = normalize_unit(match.group("unit")) or spec.default_unit
                rr = self.reference_store.find_range(code, species)

                # If the original line includes explicit ref range, prefer it, but keep version metadata.
                ref_low, ref_high, ref_unit = extract_reference_from_line(line)
                if rr and ref_low is not None and ref_high is not None:
                    rr = ReferenceRange(
                        low=ref_low,
                        high=ref_high,
                        unit=ref_unit or rr.unit,
                        source="report_inline_reference",
                        version="inline",
                    )

                normalized_value, normalized_unit, notes = convert_value(
                    code=code,
                    value=value,
                    unit=raw_unit,
                    target_unit=rr.unit if rr else spec.default_unit,
                )
                item = LabItem(
                    raw_name=raw_name,
                    canonical_code=code,
                    display_name=spec.display_name,
                    raw_value=raw_value,
                    value=value,
                    raw_unit=raw_unit,
                    unit=raw_unit,
                    normalized_value=normalized_value,
                    normalized_unit=normalized_unit,
                    reference_range=rr,
                    flag=self._flag(code, normalized_value, rr, species),
                    confidence=confidence,
                    source_line=line,
                    notes=notes,
                )
                prev = found.get(code)
                # Keep the higher confidence instance if duplicate metric appears.
                if not prev or item.confidence >= prev.confidence:
                    found[code] = item
        return list(found.values())

    @staticmethod
    def _join_lines_for_short_tokens(lines: list[OcrLine]) -> list[tuple[str, float]]:
        # OCR engines often split code/value/unit into adjacent fragments. Provide both original lines and
        # a concatenated paragraph to improve recall without losing source lines.
        pairs = [(line.text, line.confidence) for line in lines]
        if len(lines) > 1:
            text = " ".join(line.text for line in lines)
            confidence = min(line.confidence for line in lines) if lines else 1.0
            pairs.append((text, confidence))
        return pairs

    def _flag(self, code: str, value: float | None, rr: ReferenceRange | None, species: Species) -> str:
        if value is None or not rr:
            return "unknown"
        thresholds = self.reference_store.raw_thresholds(code, species)
        critical_low = thresholds.get("critical_low")
        critical_high = thresholds.get("critical_high")
        if critical_low is not None and value < float(critical_low):
            return "critical_low"
        if critical_high is not None and value > float(critical_high):
            return "critical_high"
        if rr.low is not None and value < rr.low:
            return "low"
        if rr.high is not None and value > rr.high:
            return "high"
        return "normal"

    @staticmethod
    def _quality_warnings(lines: list[OcrLine], items: list[LabItem]) -> list[str]:
        warnings: list[str] = []
        settings = get_settings()
        if not lines:
            warnings.append("未提取到 OCR 文本，请检查上传文件质量或 OCR 后端配置。")
        low_conf = [line.text for line in lines if line.confidence < settings.ocr_min_confidence]
        if low_conf:
            warnings.append(f"存在 {len(low_conf)} 条低置信 OCR 文本，解读时已降低强度。")
        no_ref = [item.canonical_code for item in items if item.reference_range is None]
        if no_ref:
            warnings.append(f"部分指标缺少参考区间：{', '.join(sorted(set(no_ref)))}。")
        if not items and lines:
            warnings.append("已识别文本但未抽取到已知化验指标，请补充清晰报告或扩展 alias 配置。")
        return warnings
