from __future__ import annotations

import argparse
import json
from pathlib import Path

from pet_report.eval.runner import EvalRunner
from pet_report.models.schemas import AnalyzeReportRequest, PetProfile, Species
from pet_report.services.report_service import ReportAnalysisService


def main() -> None:
    parser = argparse.ArgumentParser(prog="pet-report", description="Pet medical report structuring CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_text = sub.add_parser("analyze-text", help="Analyze report from raw text")
    p_text.add_argument("--text", required=True)
    p_text.add_argument("--species", default="unknown", choices=["dog", "cat", "unknown"])
    p_text.add_argument("--chief-complaint", default=None)

    p_file = sub.add_parser("analyze-file", help="Analyze uploaded file through configured OCR backend")
    p_file.add_argument("--path", required=True)
    p_file.add_argument("--species", default="unknown", choices=["dog", "cat", "unknown"])
    p_file.add_argument("--chief-complaint", default=None)

    sub.add_parser("eval", help="Run regression evaluation")

    args = parser.parse_args()
    if args.cmd == "eval":
        result = EvalRunner().run()
        print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
        raise SystemExit(0 if result.failed == 0 else 1)

    service = ReportAnalysisService()
    if args.cmd == "analyze-text":
        request = AnalyzeReportRequest(
            pet_profile=PetProfile(species=Species(args.species)),
            chief_complaint=args.chief_complaint,
            report_text=args.text,
        )
        result = service.analyze_text(request)
    elif args.cmd == "analyze-file":
        path = Path(args.path)
        request = AnalyzeReportRequest(
            pet_profile=PetProfile(species=Species(args.species)),
            chief_complaint=args.chief_complaint,
        )
        result = service.analyze_file(path.read_bytes(), path.name, request)
    else:
        parser.error("unknown command")
        return
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
