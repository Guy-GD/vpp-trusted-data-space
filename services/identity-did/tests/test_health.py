from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_health_returns_unified_response_and_trace_id(
    app: FastAPI,
    client: TestClient,
) -> None:
    response = client.get(
        "/health",
        headers={"X-Trace-Id": "trace_health_001"},
    )

    assert response.status_code == 200
    assert response.headers["X-Trace-Id"] == "trace_health_001"

    body = response.json()
    assert set(body) == {"code", "message", "data", "traceId", "timestamp"}
    assert body["data"] == {
        "service": "identity-did",
        "status": "healthy",
    }
