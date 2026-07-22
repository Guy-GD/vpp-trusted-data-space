from fastapi.testclient import TestClient

from identity_did.repository import InMemoryRepository


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
