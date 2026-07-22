from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
PUBLIC_KEY = "bW9jay1wdWJsaWMta2V5"
CHINA_TZ = ZoneInfo("Asia/Shanghai")


def subject_payload(name: str, subject_type: str = "operator") -> dict:
    return {
        "name": name,
        "type": subject_type,
        "publicKey": PUBLIC_KEY,
    }


def create_subject(name: str, subject_type: str) -> str:
    response = client.post(
        "/api/v1/identity/subjects",
        json=subject_payload(name, subject_type),
    )
    assert response.status_code == 200
    return response.json()["data"]["subjectDid"]


def authorization_payload(requester: str, owner: str) -> dict:
    expire_at = datetime.now(CHINA_TZ) + timedelta(days=7)
    return {
        "requesterDid": requester,
        "ownerDid": owner,
        "assetId": "asset_idempotency_demo",
        "purpose": "federated_training",
        "expireAt": expire_at.isoformat(timespec="seconds"),
    }


def test_same_idempotency_key_replays_first_response() -> None:
    payload = subject_payload("idempotent operator")
    first = client.post(
        "/api/v1/identity/subjects",
        json=payload,
        headers={"Idempotency-Key": "idem-subject-replay", "X-Trace-Id": "trace-first"},
    )
    second = client.post(
        "/api/v1/identity/subjects",
        json=payload,
        headers={"Idempotency-Key": "idem-subject-replay", "X-Trace-Id": "trace-second"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json() == first.json()


def test_same_idempotency_key_rejects_different_request() -> None:
    headers = {"Idempotency-Key": "idem-subject-conflict"}
    first = client.post(
        "/api/v1/identity/subjects",
        json=subject_payload("first operator"),
        headers=headers,
    )
    assert first.status_code == 200

    second = client.post(
        "/api/v1/identity/subjects",
        json=subject_payload("different operator"),
        headers=headers,
    )

    assert second.status_code == 409
    assert second.json()["code"] == 40901


def test_authorization_request_rejects_mismatched_caller_did() -> None:
    requester = create_subject("requester", "operator")
    owner = create_subject("owner", "load_aggregator")

    response = client.post(
        "/api/v1/auth/requests",
        json=authorization_payload(requester, owner),
        headers={"X-Caller-Did": owner},
    )

    assert response.status_code == 401
    assert response.json()["code"] == 40102


def test_authorization_decision_rejects_mismatched_caller_did() -> None:
    requester = create_subject("decision requester", "operator")
    owner = create_subject("decision owner", "load_aggregator")
    created = client.post(
        "/api/v1/auth/requests",
        json=authorization_payload(requester, owner),
    )
    assert created.status_code == 200
    auth_id = created.json()["data"]["authId"]

    response = client.post(
        f"/api/v1/auth/requests/{auth_id}/approve",
        json={"approverDid": owner},
        headers={"X-Caller-Did": requester},
    )

    assert response.status_code == 401
    assert response.json()["code"] == 40102
