from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Barrier

import pytest
from fastapi.testclient import TestClient

from identity_did.repository import InMemoryRepository


REQUESTER_DID = "did:vpp:operator:001"
OWNER_DID = "did:vpp:load-aggregator:001"


def authorization_payload(expire_at: str) -> dict[str, str]:
    return {
        "requesterDid": REQUESTER_DID,
        "ownerDid": OWNER_DID,
        "assetId": "asset_001",
        "purpose": "federated_training_for_day_ahead_trading",
        "expireAt": expire_at,
    }


def assert_utc_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.utcoffset() == timedelta(0)
    return parsed


def test_create_requested_authorization_from_seed_dids(
    client: TestClient,
    future_expiry: str,
) -> None:
    response = client.post(
        "/api/v1/auth/requests",
        json=authorization_payload(future_expiry),
        headers={"Idempotency-Key": "auth-1"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["authId"].startswith("auth_")
    assert data["authId"] != "auth_001"
    assert data["status"] == "requested"
    assert data["requesterDid"] == REQUESTER_DID
    assert data["ownerDid"] == OWNER_DID
    assert data["assetId"] == "asset_001"
    assert data["purpose"] == "federated_training_for_day_ahead_trading"
    assert data["decision"] is None
    assert data["reason"] is None
    assert data["approverDid"] is None
    assert data["approvedAt"] is None
    assert_utc_timestamp(data["createdAt"])
    assert_utc_timestamp(data["expireAt"])
    assert data["expireAt"].endswith("Z")


@pytest.mark.parametrize("unknown_field", ["requesterDid", "ownerDid"])
def test_create_authorization_rejects_unknown_seed_party(
    client: TestClient,
    future_expiry: str,
    unknown_field: str,
) -> None:
    payload = authorization_payload(future_expiry)
    payload[unknown_field] = "did:vpp:operator:missing"

    response = client.post("/api/v1/auth/requests", json=payload)

    assert response.status_code == 401
    assert response.json()["code"] == 40102


def test_create_authorization_rejects_mismatched_caller(
    client: TestClient,
    future_expiry: str,
) -> None:
    response = client.post(
        "/api/v1/auth/requests",
        json=authorization_payload(future_expiry),
        headers={"X-Caller-Did": OWNER_DID},
    )

    assert response.status_code == 401
    assert response.json()["code"] == 40102


@pytest.mark.parametrize(
    "expire_at",
    ["2025-12-31T23:59:59Z", "2030-01-02T00:00:00"],
)
def test_create_authorization_rejects_past_or_naive_expiry(
    client: TestClient,
    expire_at: str,
) -> None:
    response = client.post(
        "/api/v1/auth/requests",
        json=authorization_payload(expire_at),
    )

    assert response.status_code == 400
    assert response.json()["code"] == 40003


def test_authorization_idempotency_replays_data_with_current_trace(
    client: TestClient,
    repository: InMemoryRepository,
    future_expiry: str,
) -> None:
    payload = authorization_payload(future_expiry)
    first = client.post(
        "/api/v1/auth/requests",
        json=payload,
        headers={"Idempotency-Key": "auth-replay", "X-Trace-Id": "trace_first"},
    )
    second = client.post(
        "/api/v1/auth/requests",
        json=payload,
        headers={"Idempotency-Key": "auth-replay", "X-Trace-Id": "trace_second"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"]["authId"] == second.json()["data"]["authId"]
    assert second.json()["traceId"] == "trace_second"
    assert second.headers["X-Trace-Id"] == "trace_second"
    assert len(repository.authorizations) == 1


def test_authorization_idempotency_rejects_same_key_with_different_body(
    client: TestClient,
    future_expiry: str,
) -> None:
    headers = {"Idempotency-Key": "auth-conflict"}
    first = client.post(
        "/api/v1/auth/requests",
        json=authorization_payload(future_expiry),
        headers=headers,
    )
    changed = authorization_payload(future_expiry)
    changed["purpose"] = "different_purpose"
    second = client.post(
        "/api/v1/auth/requests",
        json=changed,
        headers=headers,
    )

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["code"] == 40901


def test_authorization_idempotency_creates_once_under_concurrency(
    client: TestClient,
    repository: InMemoryRepository,
    future_expiry: str,
) -> None:
    worker_count = 8
    start = Barrier(worker_count)
    payload = authorization_payload(future_expiry)

    def execute() -> str:
        start.wait()
        response = client.post(
            "/api/v1/auth/requests",
            json=payload,
            headers={"Idempotency-Key": "auth-concurrent"},
        )
        assert response.status_code == 200
        return response.json()["data"]["authId"]

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        auth_ids = list(executor.map(lambda _: execute(), range(worker_count)))

    assert len(set(auth_ids)) == 1
    assert len(repository.authorizations) == 1


def test_create_authorization_strips_public_strings(
    client: TestClient,
    future_expiry: str,
) -> None:
    payload = authorization_payload(future_expiry)
    payload.update(
        {
            "requesterDid": f"  {REQUESTER_DID}  ",
            "ownerDid": f"  {OWNER_DID}  ",
            "assetId": "  asset_trimmed  ",
            "purpose": "  federated_training  ",
        }
    )

    response = client.post("/api/v1/auth/requests", json=payload)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["requesterDid"] == REQUESTER_DID
    assert data["ownerDid"] == OWNER_DID
    assert data["assetId"] == "asset_trimmed"
    assert data["purpose"] == "federated_training"


@pytest.mark.parametrize(
    "payload_change",
    [
        {"purpose": "   "},
        {"requester_did": REQUESTER_DID},
        {"unexpected": "field"},
    ],
)
def test_create_authorization_rejects_blank_or_non_camel_case_fields(
    client: TestClient,
    future_expiry: str,
    payload_change: dict[str, str],
) -> None:
    payload = authorization_payload(future_expiry)
    payload.update(payload_change)

    response = client.post("/api/v1/auth/requests", json=payload)

    assert response.status_code == 400
    assert response.json()["code"] == 40001
