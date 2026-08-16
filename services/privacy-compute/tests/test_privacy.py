from fastapi.testclient import TestClient
from privacy_compute.main import app

client = TestClient(app)

def test_secure_aggregate():
    response = client.post(
        "/api/v1/privacy/secure-aggregate",
        headers={"Idempotency-Key": "privacy-1"},
        json={
            "trainingTaskId": "fl_task_001",
            "roundId": 1,
            "updates": [
                {
                    "participantDid": f"did:vpp:participant:{i}",
                    "sampleCount": 10,
                    "modelUpdateUri": f"memory://updates/{i}.json",
                    "updateHash": f"sha256:update{i}",
                }
                for i in range(3)
            ],
            "privacyMode": "secure_masking",
        },
    )
    data = response.json()["data"]
    assert data["aggregateId"].startswith("aggregate_")
    assert data["participantCount"] == 3
    assert data["privacyMode"] == "secure_masking"
def test_encrypt_endpoint():
    response = client.post(
        "/api/v1/privacy/model-updates/encrypt",
        json={"plaintext": "sensitive_data", "participantDid": "did:vpp:participant:1"}
    )
    assert response.status_code == 200
    assert "encryptionId" in response.json()["data"]

def test_mask_endpoint():
    response = client.post(
        "/api/v1/privacy/model-updates/mask",
        json={"updateId": "update_123", "maskingType": "random"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["maskingType"] == "random"