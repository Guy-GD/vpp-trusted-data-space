from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

PUBLIC_KEY = "bW9jay1wdWJsaWMta2V5"


def create_subject() -> dict:
    response = client.post(
        "/api/v1/identity/subjects",
        json={
            "name": "负荷聚合商 A",
            "type": "load_aggregator",
            "publicKey": PUBLIC_KEY,
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


def test_register_subject_returns_contract_fields() -> None:
    data = create_subject()

    assert data["subjectDid"].startswith("did:vpp:load-aggregator:")
    assert data["name"] == "负荷聚合商 A"
    assert data["type"] == "load_aggregator"
    assert data["status"] == "active"
    assert data["createdAt"].endswith("+08:00")


def test_register_device_links_existing_owner() -> None:
    owner = create_subject()

    response = client.post(
        "/api/v1/identity/devices",
        json={
            "deviceName": "智能电表 001",
            "deviceType": "smart_meter",
            "ownerDid": owner["subjectDid"],
            "publicKey": PUBLIC_KEY,
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["deviceDid"].startswith("did:vpp:smart-meter:")
    assert data["ownerDid"] == owner["subjectDid"]
    assert data["status"] == "active"
    assert data["createdAt"].endswith("+08:00")


def test_register_device_rejects_unknown_owner() -> None:
    response = client.post(
        "/api/v1/identity/devices",
        json={
            "deviceName": "孤立设备",
            "deviceType": "smart_meter",
            "ownerDid": "did:vpp:load-aggregator:missing",
            "publicKey": PUBLIC_KEY,
        },
        headers={"X-Trace-Id": "trace_owner_missing"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "code": 40102,
        "message": "invalid did",
        "data": None,
        "traceId": "trace_owner_missing",
    }
