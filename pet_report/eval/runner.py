from __future__ import annotations

from pathlib import Path

import yaml

from pet_report.models.schemas import AnalyzeReportRequest, EvalResult, PetProfile, Species
from pet_report.services.report_service import ReportAnalysisService


class EvalRunner:
    def __init__(self, cases_path: Path = Path("data/eval_cases.yml")) -> None:
        self.cases_path = cases_path
        self.service = ReportAnalysisService()

    def run(self) -> EvalResult:
        payload = yaml.safe_load(self.cases_path.read_text(encoding="utf-8"))
        details = []
        passed = 0
        for case in payload.get("cases", []):
            req = AnalyzeReportRequest(
                pet_profile=PetProfile(species=Species(case.get("species", "unknown"))),
                chief_complaint=case.get("text", ""),
                report_text=case.get("text", ""),
            )
            result = self.service.analyze_text(req)
            got_codes = {i.canonical_code for i in result.structured_report.lab_items}
            got_risk = {r.code for r in result.risk_alerts}
            expected_codes = set(case.get("expected_codes", []))
            expected_risk = set(case.get("expected_risk_codes", []))
            ok = expected_codes <= got_codes and expected_risk <= got_risk
            if ok:
                passed += 1
            details.append(
                {
                    "id": case.get("id"),
                    "passed": ok,
                    "expected_codes": sorted(expected_codes),
                    "got_codes": sorted(got_codes),
                    "expected_risk_codes": sorted(expected_risk),
                    "got_risk_codes": sorted(got_risk),
                }
            )
        total = len(details)
        return EvalResult(total=total, passed=passed, failed=total - passed, details=details)
