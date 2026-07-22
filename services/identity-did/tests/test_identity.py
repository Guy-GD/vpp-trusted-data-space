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
