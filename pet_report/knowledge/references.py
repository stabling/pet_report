from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from pet_report.models.schemas import ReferenceRange, Species


@dataclass(frozen=True)
class MetricSpec:
    code: str
    display_name: str
    aliases: tuple[str, ...]
    default_unit: str
    species_ranges: dict[str, dict[str, Any]]


class ReferenceRangeStore:
    def __init__(self, path: Path):
        self.path = path
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.version = str(payload.get("version", "unknown"))
        self.source = str(payload.get("source", path.name))
        self.metrics: dict[str, MetricSpec] = {}
        self.alias_to_code: dict[str, str] = {}
        for code, spec in payload.get("metrics", {}).items():
            metric = MetricSpec(
                code=code,
                display_name=spec.get("display_name", code),
                aliases=tuple(spec.get("aliases", [])),
                default_unit=spec.get("default_unit", ""),
                species_ranges=spec.get("species", {}),
            )
            self.metrics[code] = metric
            for alias in (code, *metric.aliases):
                self.alias_to_code[self._norm(alias)] = code

    @staticmethod
    def _norm(text: str) -> str:
        return text.strip().replace(" ", "").replace("：", ":").upper()

    def canonicalize(self, raw_name: str) -> tuple[str | None, MetricSpec | None]:
        key = self._norm(raw_name)
        if key in self.alias_to_code:
            code = self.alias_to_code[key]
            return code, self.metrics[code]
        for alias, code in self.alias_to_code.items():
            if alias and alias in key:
                return code, self.metrics[code]
        return None, None

    def find_range(self, code: str, species: Species) -> ReferenceRange | None:
        spec = self.metrics.get(code)
        if not spec:
            return None
        ranges = spec.species_ranges
        sp = species.value if species != Species.unknown else "dog"
        raw = ranges.get(sp) or ranges.get("dog") or next(iter(ranges.values()), None)
        if not raw:
            return None
        return ReferenceRange(
            low=raw.get("low"),
            high=raw.get("high"),
            unit=raw.get("unit", spec.default_unit),
            source=self.source,
            version=self.version,
        )

    def raw_thresholds(self, code: str, species: Species) -> dict[str, Any]:
        spec = self.metrics.get(code)
        if not spec:
            return {}
        sp = species.value if species != Species.unknown else "dog"
        return spec.species_ranges.get(sp) or spec.species_ranges.get("dog") or {}
