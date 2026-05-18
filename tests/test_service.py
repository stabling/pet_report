from pet_report.models.schemas import AnalyzeReportRequest, PetProfile, Species
from pet_report.services.report_service import ReportAnalysisService


def test_service_risk_for_cat_urinary_obstruction():
    service = ReportAnalysisService()
    req = AnalyzeReportRequest(
        pet_profile=PetProfile(species=Species.cat),
        chief_complaint="猫尿不出来，精神差",
        report_text="CREA 520 umol/L BUN 31 mmol/L",
    )
    result = service.analyze_text(req)
    codes = {i.canonical_code for i in result.structured_report.lab_items}
    risks = {r.code for r in result.risk_alerts}
    assert {"CREA", "BUN"} <= codes
    assert "urinary_obstruction" in risks
    assert "critical_lab" in risks
    assert result.citations


def test_service_conservative_summary_without_risk():
    service = ReportAnalysisService()
    req = AnalyzeReportRequest(
        pet_profile=PetProfile(species=Species.dog),
        chief_complaint="呕吐，精神一般",
        report_text="ALT 180 U/L AST 70 U/L GLU 5.8 mmol/L",
    )
    result = service.analyze_text(req)
    assert result.abnormal_findings
    assert any("肝酶" in c for c in result.combination_interpretations)
