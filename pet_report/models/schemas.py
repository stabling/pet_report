from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Species(str, Enum):
    dog = "dog"
    cat = "cat"
    unknown = "unknown"


class PetProfile(BaseModel):
    species: Species = Species.unknown
    name: str | None = None
    breed: str | None = None
    sex: str | None = None
    age_years: float | None = None
    weight_kg: float | None = None


class ReportSource(BaseModel):
    source_type: Literal["text", "image", "pdf", "unknown"] = "unknown"
    filename: str | None = None
    page_count: int | None = None
    raw_text: str | None = None


class OcrLine(BaseModel):
    text: str
    confidence: float = 1.0
    bbox: list[float] | None = None
    page: int | None = None


class ReferenceRange(BaseModel):
    low: float | None = None
    high: float | None = None
    unit: str
    source: str = "default"
    version: str = "v1"


class LabItem(BaseModel):
    raw_name: str
    canonical_code: str
    display_name: str
    raw_value: str
    value: float | None = None
    raw_unit: str | None = None
    unit: str | None = None
    normalized_value: float | None = None
    normalized_unit: str | None = None
    reference_range: ReferenceRange | None = None
    flag: Literal["low", "normal", "high", "critical_low", "critical_high", "unknown"] = "unknown"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_line: str | None = None
    notes: list[str] = Field(default_factory=list)


class RiskLevel(str, Enum):
    none = "none"
    low = "low"
    medium = "medium"
    high = "high"
    emergency = "emergency"


class RiskAlert(BaseModel):
    code: str
    level: RiskLevel
    title: str
    reason: str
    action: str
    evidence: list[str] = Field(default_factory=list)


class Evidence(BaseModel):
    id: str
    title: str
    content: str
    source: str
    score: float = 0.0
    tags: list[str] = Field(default_factory=list)


class StructuredReport(BaseModel):
    trace_id: str
    pet_profile: PetProfile
    report_source: ReportSource
    ocr_lines: list[OcrLine] = Field(default_factory=list)
    lab_items: list[LabItem] = Field(default_factory=list)
    quality_warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class InterpretationResult(BaseModel):
    trace_id: str
    structured_report: StructuredReport
    summary: str
    abnormal_findings: list[str] = Field(default_factory=list)
    combination_interpretations: list[str] = Field(default_factory=list)
    risk_alerts: list[RiskAlert] = Field(default_factory=list)
    citations: list[Evidence] = Field(default_factory=list)
    recommended_questions: list[str] = Field(default_factory=list)
    disclaimer: str = "本结果用于宠物健康信息整理和就诊沟通辅助，不能替代兽医诊断、处方或急救处置。"


class AnalyzeReportRequest(BaseModel):
    pet_profile: PetProfile = Field(default_factory=PetProfile)
    chief_complaint: str | None = None
    report_text: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalyzeReportResponse(BaseModel):
    result: InterpretationResult


class EvalCase(BaseModel):
    id: str
    species: Species
    text: str
    expected_codes: list[str] = Field(default_factory=list)
    expected_risk_codes: list[str] = Field(default_factory=list)


class EvalResult(BaseModel):
    total: int
    passed: int
    failed: int
    details: list[dict[str, Any]]
