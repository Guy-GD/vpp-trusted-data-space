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


def test_exact_business_route_surface(app: FastAPI) -> None:
    actual = {
        (method, route.path)
        for route in app.routes
        for method in (route.methods or set())
        if route.path
        not in {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}
        and method not in {"HEAD", "OPTIONS"}
    }

    assert actual == {
        ("GET", "/health"),
        ("POST", "/api/v1/identity/subjects"),
        ("POST", "/api/v1/identity/devices"),
        ("POST", "/api/v1/identity/verify"),
        ("POST", "/api/v1/auth/requests"),
        ("POST", "/api/v1/auth/requests/{authId}/approve"),
        ("GET", "/api/v1/auth/requests/{authId}"),
    }
