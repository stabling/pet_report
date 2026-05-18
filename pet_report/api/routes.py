from __future__ import annotations

import time

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from pet_report.core.security import verify_api_key
from pet_report.models.schemas import AnalyzeReportRequest, AnalyzeReportResponse, PetProfile, Species
from pet_report.observability.metrics import EXTRACTED_ITEMS, REPORT_LATENCY, REPORT_REQUESTS, RISK_ALERTS, metrics_payload
from pet_report.services.report_service import ReportAnalysisService

router = APIRouter(dependencies=[Depends(verify_api_key)])
service = ReportAnalysisService()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/v1/reports/analyze", response_model=AnalyzeReportResponse)
def analyze_report(request: AnalyzeReportRequest) -> AnalyzeReportResponse:
    start = time.perf_counter()
    try:
        result = service.analyze_text(request)
        EXTRACTED_ITEMS.observe(len(result.structured_report.lab_items))
        for alert in result.risk_alerts:
            RISK_ALERTS.labels(code=alert.code).inc()
        REPORT_REQUESTS.labels(endpoint="analyze", status="ok").inc()
        return AnalyzeReportResponse(result=result)
    except Exception as exc:
        REPORT_REQUESTS.labels(endpoint="analyze", status="error").inc()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        REPORT_LATENCY.labels(endpoint="analyze").observe(time.perf_counter() - start)


@router.post("/v1/reports/analyze-file", response_model=AnalyzeReportResponse)
async def analyze_file(
    file: UploadFile = File(...),
    species: Species = Form(default=Species.unknown),
    chief_complaint: str | None = Form(default=None),
    name: str | None = Form(default=None),
    age_years: float | None = Form(default=None),
    weight_kg: float | None = Form(default=None),
) -> AnalyzeReportResponse:
    start = time.perf_counter()
    try:
        content = await file.read()
        request = AnalyzeReportRequest(
            pet_profile=PetProfile(species=species, name=name, age_years=age_years, weight_kg=weight_kg),
            chief_complaint=chief_complaint,
        )
        result = service.analyze_file(content, file.filename, request)
        EXTRACTED_ITEMS.observe(len(result.structured_report.lab_items))
        for alert in result.risk_alerts:
            RISK_ALERTS.labels(code=alert.code).inc()
        REPORT_REQUESTS.labels(endpoint="analyze_file", status="ok").inc()
        return AnalyzeReportResponse(result=result)
    except Exception as exc:
        REPORT_REQUESTS.labels(endpoint="analyze_file", status="error").inc()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        REPORT_LATENCY.labels(endpoint="analyze_file").observe(time.perf_counter() - start)


@router.get("/metrics")
def metrics() -> Response:
    return Response(content=metrics_payload(), media_type="text/plain; version=0.0.4")
