from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Barrier
from typing import Any

import pytest
import vpp_common
from fastapi.testclient import TestClient

from identity_did.main import create_app
from identity_did.repository import InMemoryRepository
from identity_did.schemas import AuthorizationRecord


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


def decision_payload(
    decision: str = "approved",
    reason: str | None = None,
    approver_did: str = OWNER_DID,
) -> dict[str, str | None]:
    return {
        "approverDid": approver_did,
        "decision": decision,
        "reason": reason,
    }


def create_authorization(
    client: TestClient,
    expire_at: str,
    *,
    key: str,
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/auth/requests",
        json=authorization_payload(expire_at),
        headers={"Idempotency-Key": key},
    )
    assert response.status_code == 200
    return response.json()["data"]


def assert_utc_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.utcoffset() == timedelta(0)
    return parsed


def stored_authorization(auth_id: str, purpose: str) -> AuthorizationRecord:
    return AuthorizationRecord(
        authId=auth_id,
        status="requested",
        requesterDid=REQUESTER_DID,
        ownerDid=OWNER_DID,
        assetId="asset_existing",
        purpose=purpose,
        expireAt="2030-01-11T00:00:00.000Z",
        decision=None,
        reason=None,
        approverDid=None,
        createdAt="2030-01-01T00:00:00.000Z",
        approvedAt=None,
    )


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


def test_create_authorization_rejects_numeric_expiry(
    client: TestClient,
    future_expiry: str,
) -> None:
    payload: dict[str, object] = authorization_payload(future_expiry)
    payload["expireAt"] = 2524608000

    response = client.post("/api/v1/auth/requests", json=payload)

    assert response.status_code == 400
    assert response.json()["code"] == 40001


def test_expiry_must_remain_future_after_millisecond_normalization(
    client: TestClient,
    clock: Any,
) -> None:
    clock.current = datetime.fromisoformat("2030-01-01T00:00:00.123456+00:00")
    expire_at = (clock.current + timedelta(microseconds=1)).isoformat()

    response = client.post(
        "/api/v1/auth/requests",
        json=authorization_payload(expire_at),
    )

    assert response.status_code == 400
    assert response.json()["code"] == 40003


def test_creation_uses_one_now_snapshot_for_validation_and_created_at() -> None:
    class AdvancingClock:
        def __init__(self) -> None:
            self.current = datetime.fromisoformat(
                "2030-01-01T00:00:00.123456+00:00"
            )
            self.calls = 0

        def now(self) -> datetime:
            snapshot = self.current
            self.current += timedelta(days=1)
            self.calls += 1
            return snapshot

        def now_iso(self) -> str:
            return self.current.isoformat(timespec="milliseconds").replace(
                "+00:00", "Z"
            )

    clock = AdvancingClock()
    app = create_app(InMemoryRepository(), clock)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/requests",
            json=authorization_payload("2030-01-11T00:00:00Z"),
        )

    assert response.status_code == 200
    assert response.json()["data"]["createdAt"] == "2030-01-01T00:00:00.123Z"
    assert clock.calls == 1


def test_extreme_expiry_timezone_returns_controlled_invalid_timestamp(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/requests",
        json=authorization_payload("9999-12-31T23:59:59.999999-14:00"),
    )

    assert response.status_code == 400
    assert response.json()["code"] == 40003


def test_extreme_clock_timezone_returns_controlled_invalid_timestamp(
    client: TestClient,
    clock: Any,
) -> None:
    clock.current = datetime.min.replace(
        tzinfo=datetime.fromisoformat("2000-01-01T00:00:00+14:00").tzinfo
    )

    response = client.post(
        "/api/v1/auth/requests",
        json=authorization_payload("2030-01-11T00:00:00Z"),
    )

    assert response.status_code == 400
    assert response.json()["code"] == 40003


def test_falsey_clock_is_preserved_by_dependency_injection() -> None:
    class FalseyClock:
        current = datetime.fromisoformat("2040-01-01T00:00:00.456789+00:00")

        def __bool__(self) -> bool:
            return False

        def now(self) -> datetime:
            return self.current

        def now_iso(self) -> str:
            return self.current.isoformat(timespec="milliseconds").replace(
                "+00:00", "Z"
            )

    app = create_app(InMemoryRepository(), FalseyClock())
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/requests",
            json=authorization_payload("2040-01-11T00:00:00Z"),
        )

    assert response.status_code == 200
    assert response.json()["data"]["createdAt"] == "2040-01-01T00:00:00.456Z"


def test_authorization_id_collision_retries_without_overwriting(
    monkeypatch: pytest.MonkeyPatch,
    repository: InMemoryRepository,
    clock: Any,
    future_expiry: str,
) -> None:
    existing = stored_authorization("auth_collision", "existing_purpose")
    assert repository.create_authorization(existing) is not None
    generated_ids = iter(["auth_collision", "auth_after_collision"])
    monkeypatch.setattr(vpp_common, "new_id", lambda prefix: next(generated_ids))
    app = create_app(repository, clock)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/requests",
            json=authorization_payload(future_expiry),
        )

    assert response.status_code == 200
    assert response.json()["data"]["authId"] == "auth_after_collision"
    assert repository.authorizations["auth_collision"].purpose == "existing_purpose"
    assert len(repository.authorizations) == 2


def test_repository_and_response_authorizations_are_isolated_copies(
    client: TestClient,
    repository: InMemoryRepository,
    future_expiry: str,
) -> None:
    original = stored_authorization("auth_direct", "direct_purpose")
    saved = repository.create_authorization(original)
    assert saved is not None
    original.status = "approved"
    saved.status = "rejected"
    persisted = repository.get_authorization("auth_direct")
    assert persisted is not None
    assert persisted.status == "requested"

    response = client.post(
        "/api/v1/auth/requests",
        json=authorization_payload(future_expiry),
    )
    assert response.status_code == 200
    response_data = response.json()["data"]
    response_data["status"] = "approved"

    stored = repository.get_authorization(response_data["authId"])
    assert stored is not None
    stored.status = "rejected"
    fresh = repository.get_authorization(response_data["authId"])
    assert fresh is not None
    assert fresh.status == "requested"


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


def test_owner_approves_requested_authorization(
    client: TestClient,
    future_expiry: str,
) -> None:
    created = create_authorization(client, future_expiry, key="auth-approve-flow")

    response = client.post(
        f"/api/v1/auth/requests/{created['authId']}/approve",
        json=decision_payload(),
        headers={"Idempotency-Key": "approve-flow"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "approved"
    assert data["decision"] == "approved"
    assert data["reason"] is None
    assert data["approverDid"] == OWNER_DID
    assert data["approvedAt"].endswith("Z")
    assert_utc_timestamp(data["approvedAt"])

    queried = client.get(f"/api/v1/auth/requests/{created['authId']}")
    assert queried.status_code == 200
    assert queried.json()["data"] == data


def test_owner_rejects_requested_authorization_with_reason(
    client: TestClient,
    future_expiry: str,
) -> None:
    created = create_authorization(client, future_expiry, key="auth-reject-flow")

    response = client.post(
        f"/api/v1/auth/requests/{created['authId']}/approve",
        json=decision_payload("rejected", "purpose not permitted"),
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "rejected"
    assert data["decision"] == "rejected"
    assert data["reason"] == "purpose not permitted"
    assert data["approverDid"] == OWNER_DID
    assert data["approvedAt"].endswith("Z")


def test_unknown_authorization_returns_40401(client: TestClient) -> None:
    approve = client.post(
        "/api/v1/auth/requests/auth_missing/approve",
        json=decision_payload(),
    )
    query = client.get("/api/v1/auth/requests/auth_missing")

    for response in (approve, query):
        assert response.status_code == 404
        assert response.json()["code"] == 40401


def test_non_owner_cannot_decide_authorization(
    client: TestClient,
    future_expiry: str,
) -> None:
    created = create_authorization(client, future_expiry, key="auth-wrong-owner")

    response = client.post(
        f"/api/v1/auth/requests/{created['authId']}/approve",
        json=decision_payload(approver_did=REQUESTER_DID),
    )

    assert response.status_code == 403
    assert response.json()["code"] == 40301


def test_approval_rejects_mismatched_caller_header(
    client: TestClient,
    future_expiry: str,
) -> None:
    created = create_authorization(client, future_expiry, key="auth-approval-caller")

    response = client.post(
        f"/api/v1/auth/requests/{created['authId']}/approve",
        json=decision_payload(),
        headers={"X-Caller-Did": REQUESTER_DID},
    )

    assert response.status_code == 401
    assert response.json()["code"] == 40102


def test_decided_authorization_rejects_second_decision(
    client: TestClient,
    future_expiry: str,
) -> None:
    created = create_authorization(client, future_expiry, key="auth-duplicate")
    endpoint = f"/api/v1/auth/requests/{created['authId']}/approve"
    first = client.post(endpoint, json=decision_payload())
    second = client.post(endpoint, json=decision_payload("rejected"))

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["code"] == 40902


def test_approval_idempotency_replays_data_with_fresh_trace(
    client: TestClient,
    future_expiry: str,
) -> None:
    created = create_authorization(client, future_expiry, key="auth-approve-replay")
    endpoint = f"/api/v1/auth/requests/{created['authId']}/approve"
    payload = decision_payload(reason="approved for demo")
    first = client.post(
        endpoint,
        json=payload,
        headers={
            "Idempotency-Key": "approval-replay",
            "X-Trace-Id": "trace_approval_1",
        },
    )
    second = client.post(
        endpoint,
        json=payload,
        headers={
            "Idempotency-Key": "approval-replay",
            "X-Trace-Id": "trace_approval_2",
        },
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["data"] == first.json()["data"]
    assert second.json()["traceId"] == "trace_approval_2"
    assert second.headers["X-Trace-Id"] == "trace_approval_2"


def test_approval_rejects_blank_idempotency_key(
    client: TestClient,
    future_expiry: str,
) -> None:
    created = create_authorization(client, future_expiry, key="auth-blank-key")

    response = client.post(
        f"/api/v1/auth/requests/{created['authId']}/approve",
        json=decision_payload(),
        headers={"Idempotency-Key": "   "},
    )

    assert response.status_code == 400
    assert response.json()["code"] == 40001


def test_approved_authorization_expires_on_query_and_stays_expired(
    client: TestClient,
    repository: InMemoryRepository,
    clock: Any,
) -> None:
    expire_at = (clock.now() + timedelta(hours=1)).isoformat()
    created = create_authorization(client, expire_at, key="auth-expiry")
    endpoint = f"/api/v1/auth/requests/{created['authId']}"
    approved = client.post(
        f"{endpoint}/approve",
        json=decision_payload(),
    )
    assert approved.status_code == 200

    clock.advance(timedelta(hours=2))
    queried = client.get(endpoint)

    assert queried.status_code == 403
    assert queried.json()["code"] == 40303
    stored = repository.get_authorization(created["authId"])
    assert stored is not None
    assert stored.status == "expired"

    decided_again = client.post(
        f"{endpoint}/approve",
        json=decision_payload(),
    )
    assert decided_again.status_code == 403
    assert decided_again.json()["code"] == 40303


def test_concurrent_decisions_allow_at_most_one_success(
    client: TestClient,
    repository: InMemoryRepository,
    future_expiry: str,
) -> None:
    created = create_authorization(client, future_expiry, key="auth-race")
    endpoint = f"/api/v1/auth/requests/{created['authId']}/approve"
    worker_count = 8
    start = Barrier(worker_count)

    def decide(index: int) -> tuple[int, int]:
        start.wait()
        decision = "approved" if index % 2 == 0 else "rejected"
        response = client.post(
            endpoint,
            json=decision_payload(decision),
        )
        return response.status_code, response.json()["code"]

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        results = list(executor.map(decide, range(worker_count)))

    assert sum(status == 200 for status, _ in results) == 1
    assert all(
        (status, code) == (200, 0) or (status, code) == (409, 40902)
        for status, code in results
    )
    stored = repository.get_authorization(created["authId"])
    assert stored is not None
    assert stored.status in {"approved", "rejected"}
