from __future__ import annotations

from pet_report.core.config import get_settings
from pet_report.core.trace import new_trace_id
from pet_report.interpretation.rules import RuleInterpreter
from pet_report.knowledge.references import ReferenceRangeStore
from pet_report.llm.factory import build_generator
from pet_report.models.schemas import (
    AnalyzeReportRequest,
    InterpretationResult,
    OcrLine,
    ReportSource,
)
from pet_report.ocr.factory import build_ocr_backend
from pet_report.rag.retriever import LocalKnowledgeRetriever
from pet_report.safety.risk import RiskGate
from pet_report.structuring.parser import ReportStructurer


class ReportAnalysisService:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.ocr = build_ocr_backend()
        self.references = ReferenceRangeStore(settings.reference_path)
        self.structurer = ReportStructurer(self.references)
        self.rag = LocalKnowledgeRetriever(settings.knowledge_path)
        self.risk_gate = RiskGate()
        self.rule_interpreter = RuleInterpreter()
        self.generator = build_generator()

    def analyze_text(self, request: AnalyzeReportRequest, trace_id: str | None = None) -> InterpretationResult:
        trace_id = trace_id or new_trace_id()
        text = request.report_text or ""
        lines = [OcrLine(text=line.strip(), confidence=1.0) for line in text.splitlines() if line.strip()]
        if not lines and text.strip():
            lines = [OcrLine(text=text.strip(), confidence=1.0)]
        source = ReportSource(source_type="text", raw_text=text)
        return self._analyze_lines(lines, request, source, trace_id)

    def analyze_file(
        self,
        content: bytes,
        filename: str | None,
        request: AnalyzeReportRequest,
        trace_id: str | None = None,
    ) -> InterpretationResult:
        trace_id = trace_id or new_trace_id()
        if len(content) > self.settings.max_report_size_bytes:
            raise ValueError(f"file too large, max={self.settings.max_report_size_mb}MB")
        source_type = self._source_type(filename)
        lines = self.ocr.extract(content, filename=filename)
        source = ReportSource(source_type=source_type, filename=filename, raw_text="\n".join(l.text for l in lines))
        return self._analyze_lines(lines, request, source, trace_id)

    def _analyze_lines(
        self,
        lines: list[OcrLine],
        request: AnalyzeReportRequest,
        source: ReportSource,
        trace_id: str,
    ) -> InterpretationResult:
        structured = self.structurer.structure(lines, request.pet_profile, source, trace_id=trace_id)
        risk_alerts = self.risk_gate.evaluate(
            request.chief_complaint,
            structured.lab_items,
            request.pet_profile,
        ) if self.settings.enable_risk_gate else []
        query = " ".join(filter(None, [request.chief_complaint or "", source.raw_text or ""]))
        citations = self.rag.retrieve(query, structured.lab_items, top_k=5) if self.settings.enable_rag else []
        summary, abnormal, combos, questions = self.rule_interpreter.build(
            lab_items=structured.lab_items,
            pet_profile=request.pet_profile,
            chief_complaint=request.chief_complaint,
            risk_alerts=risk_alerts,
            citations=citations,
        )
        summary, abnormal, combos, questions = self.generator.generate(
            summary=summary,
            abnormal=abnormal,
            combos=combos,
            questions=questions,
            lab_items=structured.lab_items,
            pet_profile=request.pet_profile,
            risk_alerts=risk_alerts,
            citations=citations,
        )
        return InterpretationResult(
            trace_id=trace_id,
            structured_report=structured,
            summary=summary,
            abnormal_findings=abnormal,
            combination_interpretations=combos,
            risk_alerts=risk_alerts,
            citations=citations,
            recommended_questions=questions,
        )

    @staticmethod
    def _source_type(filename: str | None) -> str:
        if not filename:
            return "unknown"
        lower = filename.lower()
        if lower.endswith(".pdf"):
            return "pdf"
        if lower.endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")):
            return "image"
        if lower.endswith((".txt", ".csv", ".md")):
            return "text"
        return "unknown"
