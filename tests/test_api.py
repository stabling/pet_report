from fastapi.testclient import TestClient

from pet_report.main import app


def test_health():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_analyze_api():
    client = TestClient(app)
    resp = client.post(
        "/v1/reports/analyze",
        json={
            "pet_profile": {"species": "dog"},
            "chief_complaint": "食欲下降",
            "report_text": "WBC 24.5 10^9/L HGB 88 g/L",
        },
    )
    assert resp.status_code == 200, resp.text
    payload = resp.json()["result"]
    codes = {i["canonical_code"] for i in payload["structured_report"]["lab_items"]}
    assert {"WBC", "HGB"} <= codes


def test_metrics():
    client = TestClient(app)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "pet_report_requests_total" in resp.text
