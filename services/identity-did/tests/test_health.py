from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_returns_unified_response_and_trace_id() -> None:
    response = client.get(
        "/health",
        headers={"X-Trace-Id": "trace_health_001"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "code": 0,
        "message": "ok",
        "data": {
            "service": "identity-did",
            "status": "healthy",
        },
        "traceId": "trace_health_001",
    }
