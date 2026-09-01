from fastapi.testclient import TestClient

from api_gateway.main import app


client = TestClient(app)


def test_health():

    response = client.get(
        "/api/v1/health"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["code"] == 0
    assert "timestamp" in body
    assert body["traceId"].startswith("trace_")
    assert (
        body["data"]["status"]
        == "healthy"
    )
    