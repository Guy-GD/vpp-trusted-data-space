from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_missing_required_field_uses_common_error_envelope() -> None:
    response = client.post(
        "/api/v1/identity/subjects",
        json={
            "type": "load_aggregator",
            "publicKey": "bW9jay1wdWJsaWMta2V5",
        },
        headers={"X-Trace-Id": "trace_missing_001"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": 40002,
        "message": "missing required field",
        "data": None,
        "traceId": "trace_missing_001",
    }


def test_invalid_field_uses_common_error_envelope() -> None:
    response = client.post(
        "/api/v1/identity/subjects",
        json={
            "name": "",
            "type": "load_aggregator",
            "publicKey": "bW9jay1wdWJsaWMta2V5",
        },
        headers={"X-Trace-Id": "trace_invalid_001"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": 40001,
        "message": "invalid request",
        "data": None,
        "traceId": "trace_invalid_001",
    }
