from fastapi.testclient import TestClient

from api_gateway.main import app

PAYLOAD = {
    "scenario": "vpp_day_ahead_trading",
    "participants": ["aggregator-A", "energy-user-B"],
    "meterCount": 3,
    "trainingRounds": 2,
}


def test_demo_workflow(app_workflow):
    client = TestClient(app)

    response = client.post("/api/v1/demo/run", json=PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert "timestamp" in body
    assert body["traceId"].startswith("trace_")

    data = body["data"]
    assert data["status"] == "COMPLETED"
    assert data["businessId"].startswith("demo_")
    assert data["assetId"].startswith("asset_")
    assert data["globalModelVersion"].startswith("global_model_v")
    assert data["agentReportId"].startswith("report_")


def test_idempotency_same_key_same_request_returns_same_business_id(app_workflow):
    client = TestClient(app)
    headers = {"Idempotency-Key": "demo-key-1"}

    first = client.post("/api/v1/demo/run", json=PAYLOAD, headers=headers)
    second = client.post("/api/v1/demo/run", json=PAYLOAD, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"]["businessId"] == second.json()["data"]["businessId"]


def test_idempotency_same_key_different_request_returns_40901(app_workflow):
    client = TestClient(app)
    headers = {"Idempotency-Key": "demo-key-2"}

    client.post("/api/v1/demo/run", json=PAYLOAD, headers=headers)
    changed = {**PAYLOAD, "trainingRounds": 5}
    response = client.post("/api/v1/demo/run", json=changed, headers=headers)

    assert response.status_code == 409
    body = response.json()
    assert body["code"] == 40901
    assert body["traceId"].startswith("trace_")


def test_status_query_returns_completed(app_workflow):
    client = TestClient(app)

    run = client.post("/api/v1/demo/run", json=PAYLOAD)
    business_id = run.json()["data"]["businessId"]

    status = client.get(f"/api/v1/demo/status/{business_id}")
    assert status.status_code == 200
    assert status.json()["data"]["status"] == "COMPLETED"