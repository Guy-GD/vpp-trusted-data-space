import base64
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi.testclient import TestClient

from identity_did.repository import InMemoryRepository
from identity_did.schemas import SubjectCreateRequest, SubjectRecord
from identity_did.service import IdentityService


DEMO_DIDS = {
    "did:vpp:operator:001",
    "did:vpp:load-aggregator:001",
    "did:vpp:renewable-plant:001",
    "did:vpp:storage:001",
}
PUBLIC_KEY = "bW9jay1wdWJsaWMta2V5"
PAYLOAD_HASH = f"sha256:{'a' * 64}"


def mock_signature(public_key: str, payload_hash: str) -> str:
    digest = hashlib.sha256(
        f"{public_key}:{payload_hash}".encode("utf-8")
    ).digest()
    return base64.b64encode(digest).decode("ascii")


def test_repository_contains_four_active_demo_subjects(
    repository: InMemoryRepository,
) -> None:
    assert set(repository.subjects) == DEMO_DIDS
    assert {
        record.type for record in repository.subjects.values()
    } == {
        "operator",
        "load_aggregator",
        "renewable_plant",
        "storage",
    }
    assert all(
        record.status == "active" and record.publicKey == PUBLIC_KEY
        for record in repository.subjects.values()
    )
    assert repository.devices == {}
    assert repository.authorizations == {}
    assert repository.idempotency == {}


def test_register_subject_returns_frozen_fields_without_overwriting_seed(
    client: TestClient,
    repository: InMemoryRepository,
) -> None:
    seed = repository.subjects["did:vpp:operator:001"]

    response = client.post(
        "/api/v1/identity/subjects",
        json={
            "name": "Backup operator",
            "type": "operator",
            "publicKey": PUBLIC_KEY,
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert set(data) == {"subjectDid", "name", "type", "status", "createdAt"}
    assert data["subjectDid"] == "did:vpp:operator:002"
    assert data["subjectDid"] != seed.subjectDid
    assert data["name"] == "Backup operator"
    assert data["type"] == "operator"
    assert data["status"] == "active"
    assert data["createdAt"]
    assert repository.subjects[seed.subjectDid] is seed
    assert repository.subjects[data["subjectDid"]].publicKey == PUBLIC_KEY


def test_register_device_links_an_existing_active_owner(
    client: TestClient,
    repository: InMemoryRepository,
) -> None:
    owner_did = "did:vpp:load-aggregator:001"

    response = client.post(
        "/api/v1/identity/devices",
        json={
            "deviceName": "Smart meter 001",
            "deviceType": "smart_meter",
            "ownerDid": owner_did,
            "publicKey": PUBLIC_KEY,
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert set(data) == {"deviceDid", "ownerDid", "status", "createdAt"}
    assert data["deviceDid"].startswith("did:vpp:smart-meter:")
    assert data["ownerDid"] == owner_did
    assert data["status"] == "active"
    assert data["createdAt"]
    stored = repository.devices[data["deviceDid"]]
    assert stored.ownerDid == owner_did
    assert stored.publicKey == PUBLIC_KEY


def test_register_device_rejects_unknown_owner(client: TestClient) -> None:
    response = client.post(
        "/api/v1/identity/devices",
        headers={"X-Trace-Id": "trace_unknown_owner"},
        json={
            "deviceName": "Orphan meter",
            "deviceType": "smart_meter",
            "ownerDid": "did:vpp:operator:missing",
            "publicKey": PUBLIC_KEY,
        },
    )

    assert response.status_code == 401
    body = response.json()
    assert body["code"] == 40102
    assert body["message"] == "invalid did"
    assert body["data"] is None
    assert body["traceId"] == "trace_unknown_owner"


@pytest.mark.parametrize("subject_type", ["   ", "主体"])
def test_register_subject_rejects_type_without_an_ascii_slug(
    client: TestClient,
    subject_type: str,
) -> None:
    response = client.post(
        "/api/v1/identity/subjects",
        json={
            "name": "Invalid subject",
            "type": subject_type,
            "publicKey": PUBLIC_KEY,
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == 40001


def test_register_device_rejects_internal_snake_case_field_names(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/identity/devices",
        json={
            "device_name": "Internal meter",
            "device_type": "smart_meter",
            "owner_did": "did:vpp:operator:001",
            "public_key": PUBLIC_KEY,
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == 40001


@pytest.mark.parametrize(
    ("path", "payload"),
    [
        (
            "/api/v1/identity/subjects",
            {"name": "   ", "type": "operator", "publicKey": PUBLIC_KEY},
        ),
        (
            "/api/v1/identity/subjects",
            {"name": "Subject", "type": "operator", "publicKey": "\t"},
        ),
        (
            "/api/v1/identity/devices",
            {
                "deviceName": "   ",
                "deviceType": "smart_meter",
                "ownerDid": "did:vpp:operator:001",
                "publicKey": PUBLIC_KEY,
            },
        ),
    ],
)
def test_registration_rejects_blank_public_strings(
    client: TestClient,
    path: str,
    payload: dict[str, str],
) -> None:
    response = client.post(path, json=payload)

    assert response.status_code == 400
    assert response.json()["code"] == 40001


def test_register_subject_strips_public_strings(
    client: TestClient,
    repository: InMemoryRepository,
) -> None:
    response = client.post(
        "/api/v1/identity/subjects",
        json={
            "name": "  Trimmed subject  ",
            "type": "  flexible_operator  ",
            "publicKey": f"  {PUBLIC_KEY}  ",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "Trimmed subject"
    assert data["type"] == "flexible_operator"
    assert repository.subjects[data["subjectDid"]].publicKey == PUBLIC_KEY


def test_concurrent_subject_registration_preserves_every_unique_record(
    repository: InMemoryRepository,
) -> None:
    worker_count = 8
    start = Barrier(worker_count)

    class YieldingCounter(dict[str, int]):
        def get(self, key: str, default: int = 0) -> int:
            value = super().get(key, default)
            time.sleep(0.01)
            return value

    class YieldingSubjects(dict[str, SubjectRecord]):
        def __contains__(self, key: object) -> bool:
            contains = super().__contains__(key)
            time.sleep(0.01)
            return contains

    repository._subject_counters = YieldingCounter()
    repository.subjects = YieldingSubjects(repository.subjects)
    service = IdentityService(repository)

    def register(index: int) -> str:
        request = SubjectCreateRequest(
            name=f"Concurrent subject {index}",
            type="concurrent_operator",
            publicKey=PUBLIC_KEY,
        )
        start.wait()
        return service.register_subject(request)["subjectDid"]

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        dids = list(executor.map(register, range(worker_count)))

    assert len(set(dids)) == worker_count
    assert sum(
        record.type == "concurrent_operator"
        for record in repository.subjects.values()
    ) == worker_count


def test_verify_seed_subject_with_valid_mock_signature(client: TestClient) -> None:
    subject_did = "did:vpp:operator:001"

    response = client.post(
        "/api/v1/identity/verify",
        json={
            "subjectDid": subject_did,
            "signature": mock_signature(PUBLIC_KEY, PAYLOAD_HASH),
            "payloadHash": PAYLOAD_HASH,
        },
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "valid": True,
        "did": subject_did,
        "subjectType": "operator",
    }


def test_verify_registered_device_returns_device_type(client: TestClient) -> None:
    created = client.post(
        "/api/v1/identity/devices",
        json={
            "deviceName": "Verification meter",
            "deviceType": "smart_meter",
            "ownerDid": "did:vpp:operator:001",
            "publicKey": PUBLIC_KEY,
        },
    )
    assert created.status_code == 200
    device_did = created.json()["data"]["deviceDid"]

    response = client.post(
        "/api/v1/identity/verify",
        json={
            "deviceDid": device_did,
            "signature": mock_signature(PUBLIC_KEY, PAYLOAD_HASH),
            "payloadHash": PAYLOAD_HASH,
        },
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "valid": True,
        "did": device_did,
        "subjectType": "smart_meter",
    }


def test_verify_rejects_unknown_did(client: TestClient) -> None:
    response = client.post(
        "/api/v1/identity/verify",
        json={
            "subjectDid": "did:vpp:operator:missing",
            "signature": mock_signature(PUBLIC_KEY, PAYLOAD_HASH),
            "payloadHash": PAYLOAD_HASH,
        },
    )

    assert response.status_code == 401
    assert response.json()["code"] == 40102


def test_verify_rejects_invalid_signature(client: TestClient) -> None:
    response = client.post(
        "/api/v1/identity/verify",
        json={
            "subjectDid": "did:vpp:operator:001",
            "signature": "aW52YWxpZC1zaWduYXR1cmU=",
            "payloadHash": PAYLOAD_HASH,
        },
    )

    assert response.status_code == 401
    assert response.json()["code"] == 40103


def test_verify_rejects_non_ascii_signature(client: TestClient) -> None:
    response = client.post(
        "/api/v1/identity/verify",
        json={
            "subjectDid": "did:vpp:operator:001",
            "signature": "签名",
            "payloadHash": PAYLOAD_HASH,
        },
    )

    assert response.status_code == 401
    assert response.json()["code"] == 40103


def test_verify_rejects_invalid_base64_signature(client: TestClient) -> None:
    response = client.post(
        "/api/v1/identity/verify",
        json={
            "subjectDid": "did:vpp:operator:001",
            "signature": "%%%not-base64%%%",
            "payloadHash": PAYLOAD_HASH,
        },
    )

    assert response.status_code == 401
    assert response.json()["code"] == 40103


def test_verify_rejects_malformed_payload_hash(client: TestClient) -> None:
    response = client.post(
        "/api/v1/identity/verify",
        json={
            "subjectDid": "did:vpp:operator:001",
            "signature": "aW52YWxpZA==",
            "payloadHash": "sha256:not-hex",
        },
    )

    assert response.status_code == 401
    assert response.json()["code"] == 40104


@pytest.mark.parametrize(
    "did_fields",
    [
        {},
        {
            "subjectDid": "did:vpp:operator:001",
            "deviceDid": "did:vpp:smart-meter:001",
        },
    ],
)
def test_verify_requires_exactly_one_identity_field(
    client: TestClient,
    did_fields: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/identity/verify",
        json={
            **did_fields,
            "signature": mock_signature(PUBLIC_KEY, PAYLOAD_HASH),
            "payloadHash": PAYLOAD_HASH,
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == 40001


def test_subject_idempotency_replays_business_data_with_current_trace(
    client: TestClient,
    repository: InMemoryRepository,
) -> None:
    payload = {
        "name": "Idempotent operator",
        "type": "operator",
        "publicKey": PUBLIC_KEY,
    }
    first = client.post(
        "/api/v1/identity/subjects",
        json=payload,
        headers={
            "Idempotency-Key": "idem-subject-replay",
            "X-Trace-Id": "trace_first",
        },
    )
    second = client.post(
        "/api/v1/identity/subjects",
        json=payload,
        headers={
            "Idempotency-Key": "idem-subject-replay",
            "X-Trace-Id": "trace_second",
        },
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"]["subjectDid"] == second.json()["data"]["subjectDid"]
    assert second.json()["traceId"] == "trace_second"
    assert second.headers["X-Trace-Id"] == "trace_second"
    stored = repository.idempotency["idem-subject-replay"]
    assert stored.data == first.json()["data"]
    assert "traceId" not in stored.data
    assert "timestamp" not in stored.data


def test_subject_idempotency_rejects_same_key_with_different_body(
    client: TestClient,
) -> None:
    headers = {"Idempotency-Key": "idem-subject-conflict"}
    first = client.post(
        "/api/v1/identity/subjects",
        json={"name": "First", "type": "operator", "publicKey": PUBLIC_KEY},
        headers=headers,
    )
    assert first.status_code == 200

    second = client.post(
        "/api/v1/identity/subjects",
        json={"name": "Second", "type": "operator", "publicKey": PUBLIC_KEY},
        headers=headers,
    )

    assert second.status_code == 409
    assert second.json()["code"] == 40901


@pytest.mark.parametrize("blank_key", ["", "   \t"])
def test_subject_rejects_blank_idempotency_key_without_polluting_next_request(
    client: TestClient,
    repository: InMemoryRepository,
    blank_key: str,
) -> None:
    rejected = client.post(
        "/api/v1/identity/subjects",
        json={
            "name": "Rejected blank-key subject",
            "type": "operator",
            "publicKey": PUBLIC_KEY,
        },
        headers={"Idempotency-Key": blank_key},
    )
    follow_up = client.post(
        "/api/v1/identity/subjects",
        json={
            "name": "Normal subject after blank key",
            "type": "operator",
            "publicKey": PUBLIC_KEY,
        },
    )

    assert rejected.status_code == 400
    assert rejected.json()["code"] == 40001
    assert follow_up.status_code == 200
    assert follow_up.json()["data"]["subjectDid"] == "did:vpp:operator:002"
    assert blank_key not in repository.idempotency


def test_subject_idempotency_key_is_trimmed_before_replay(
    client: TestClient,
) -> None:
    payload = {
        "name": "Trimmed idempotency key",
        "type": "operator",
        "publicKey": PUBLIC_KEY,
    }
    first = client.post(
        "/api/v1/identity/subjects",
        json=payload,
        headers={"Idempotency-Key": "  idem-trimmed  "},
    )
    second = client.post(
        "/api/v1/identity/subjects",
        json=payload,
        headers={"Idempotency-Key": "idem-trimmed"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"]["subjectDid"] == second.json()["data"]["subjectDid"]


def test_device_idempotency_replays_same_device(client: TestClient) -> None:
    payload = {
        "deviceName": "Idempotent meter",
        "deviceType": "smart_meter",
        "ownerDid": "did:vpp:operator:001",
        "publicKey": PUBLIC_KEY,
    }
    headers = {"Idempotency-Key": "idem-device-replay"}

    first = client.post("/api/v1/identity/devices", json=payload, headers=headers)
    second = client.post("/api/v1/identity/devices", json=payload, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"] == second.json()["data"]


def test_verify_idempotency_replays_same_business_data(
    client: TestClient,
    repository: InMemoryRepository,
) -> None:
    payload = {
        "subjectDid": "did:vpp:operator:001",
        "signature": mock_signature(PUBLIC_KEY, PAYLOAD_HASH),
        "payloadHash": PAYLOAD_HASH,
    }
    headers = {"Idempotency-Key": "idem-verify-replay"}

    first = client.post("/api/v1/identity/verify", json=payload, headers=headers)
    repository.subjects["did:vpp:operator:001"].status = "inactive"
    second = client.post("/api/v1/identity/verify", json=payload, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"] == second.json()["data"]


def test_idempotency_executes_concurrent_same_key_once(
    client: TestClient,
    repository: InMemoryRepository,
) -> None:
    worker_count = 8
    start = Barrier(worker_count)
    payload = {
        "name": "Concurrent idempotent operator",
        "type": "concurrent_idempotent",
        "publicKey": PUBLIC_KEY,
    }

    def execute() -> str:
        start.wait()
        response = client.post(
            "/api/v1/identity/subjects",
            json=payload,
            headers={"Idempotency-Key": "idem-concurrent"},
        )
        assert response.status_code == 200
        return response.json()["data"]["subjectDid"]

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        subject_dids = list(executor.map(lambda _: execute(), range(worker_count)))

    assert len(set(subject_dids)) == 1
    assert sum(
        subject.type == "concurrent_idempotent"
        for subject in repository.subjects.values()
    ) == 1


def test_router_exposes_only_frozen_identity_and_authorization_routes(app) -> None:
    paths = {
        route.path
        for route in app.routes
        if not route.path.startswith(("/docs", "/redoc", "/openapi.json"))
    }

    assert paths == {
        "/health",
        "/api/v1/identity/subjects",
        "/api/v1/identity/devices",
        "/api/v1/identity/verify",
        "/api/v1/auth/requests",
        "/api/v1/auth/requests/{authId}/approve",
        "/api/v1/auth/requests/{authId}",
    }
