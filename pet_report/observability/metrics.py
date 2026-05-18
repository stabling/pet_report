from __future__ import annotations

from prometheus_client import Counter, Histogram, generate_latest

REPORT_REQUESTS = Counter("pet_report_requests_total", "Report analysis requests", ["endpoint", "status"])
REPORT_LATENCY = Histogram("pet_report_latency_seconds", "Report analysis latency", ["endpoint"])
EXTRACTED_ITEMS = Histogram("pet_report_extracted_items", "Number of structured lab items")
RISK_ALERTS = Counter("pet_report_risk_alerts_total", "Risk alerts emitted", ["code"])


def metrics_payload() -> bytes:
    return generate_latest()
