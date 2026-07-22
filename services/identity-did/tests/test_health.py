from datetime import datetime, timedelta

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
    assert body["code"] == 0
    assert body["message"] == "ok"
    assert body["data"] == {
        "service": "identity-did",
        "status": "healthy",
    }
    assert body["traceId"] == "trace_health_001"
    assert body["traceId"] == response.headers["X-Trace-Id"]

    timestamp = datetime.fromisoformat(body["timestamp"].replace("Z", "+00:00"))
    assert timestamp.utcoffset() == timedelta(0)
