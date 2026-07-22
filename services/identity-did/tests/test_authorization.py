from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
PUBLIC_KEY = "bW9jay1wdWJsaWMta2V5"
CHINA_TZ = ZoneInfo("Asia/Shanghai")


def create_subject(name: str, subject_type: str) -> str:
    response = client.post(
        "/api/v1/identity/subjects",
        json={"name": name, "type": subject_type, "publicKey": PUBLIC_KEY},
    )
    assert response.status_code == 200
    return response.json()["data"]["subjectDid"]


def future_time() -> str:
    return (datetime.now(CHINA_TZ) + timedelta(days=7)).isoformat(timespec="seconds")


def create_authorization() -> tuple[dict, str, str]:
    requester = create_subject("运营方", "operator")
    owner = create_subject("数据所有者", "load_aggregator")
    response = client.post(
        "/api/v1/auth/requests",
        json={
            "requesterDid": requester,
            "ownerDid": owner,
            "assetId": "asset_001",
            "purpose": "federated_training_for_day_ahead_trading",
            "expireAt": future_time(),
        },
    )
    assert response.status_code == 200
    return response.json()["data"], requester, owner


def test_create_and_query_pending_authorization() -> None:
    authorization, requester, owner = create_authorization()

    assert authorization["authId"].startswith("auth_")
    assert authorization["status"] == "pending"
    assert authorization["requesterDid"] == requester
    assert authorization["ownerDid"] == owner
    assert authorization["assetId"] == "asset_001"

    response = client.get(f"/api/v1/auth/requests/{authorization['authId']}")
    assert response.status_code == 200
    assert response.json()["data"] == authorization


def test_owner_can_approve_authorization() -> None:
    authorization, _, owner = create_authorization()

    response = client.post(
        f"/api/v1/auth/requests/{authorization['authId']}/approve",
        json={"approverDid": owner},
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "approved"
    assert response.json()["data"]["approverDid"] == owner


def test_owner_can_reject_authorization() -> None:
    authorization, _, owner = create_authorization()

    response = client.post(
        f"/api/v1/auth/requests/{authorization['authId']}/approve",
        json={
            "approverDid": owner,
            "decision": "rejected",
            "reason": "purpose not allowed",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "rejected"
    assert response.json()["data"]["reason"] == "purpose not allowed"


def test_create_authorization_rejects_unknown_requester() -> None:
    owner = create_subject("数据所有者", "load_aggregator")
    response = client.post(
        "/api/v1/auth/requests",
        json={
            "requesterDid": "did:vpp:operator:missing",
            "ownerDid": owner,
            "assetId": "asset_001",
            "purpose": "federated_training",
            "expireAt": future_time(),
        },
    )

    assert response.status_code == 401
    assert response.json()["code"] == 40102


def test_create_authorization_rejects_unknown_owner() -> None:
    requester = create_subject("requester with missing owner", "operator")
    response = client.post(
        "/api/v1/auth/requests",
        json={
            "requesterDid": requester,
            "ownerDid": "did:vpp:load-aggregator:missing",
            "assetId": "asset_001",
            "purpose": "federated_training",
            "expireAt": future_time(),
        },
    )

    assert response.status_code == 401
    assert response.json()["code"] == 40102


def test_create_authorization_rejects_past_expiry() -> None:
    requester = create_subject("运营方", "operator")
    owner = create_subject("数据所有者", "load_aggregator")
    past = (datetime.now(CHINA_TZ) - timedelta(minutes=1)).isoformat(timespec="seconds")

    response = client.post(
        "/api/v1/auth/requests",
        json={
            "requesterDid": requester,
            "ownerDid": owner,
            "assetId": "asset_001",
            "purpose": "federated_training",
            "expireAt": past,
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == 40003


def test_non_owner_cannot_approve_authorization() -> None:
    authorization, requester, _ = create_authorization()

    response = client.post(
        f"/api/v1/auth/requests/{authorization['authId']}/approve",
        json={"approverDid": requester},
    )

    assert response.status_code == 403
    assert response.json()["code"] == 40301


def test_query_unknown_authorization_returns_not_found() -> None:
    response = client.get("/api/v1/auth/requests/auth_missing")

    assert response.status_code == 404
    assert response.json()["code"] == 40401


def test_decided_authorization_cannot_be_decided_again() -> None:
    authorization, _, owner = create_authorization()
    path = f"/api/v1/auth/requests/{authorization['authId']}/approve"
    first = client.post(path, json={"approverDid": owner})
    assert first.status_code == 200

    second = client.post(path, json={"approverDid": owner})

    assert second.status_code == 409
    assert second.json()["code"] == 40902
