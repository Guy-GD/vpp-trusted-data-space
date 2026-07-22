import base64
import hashlib

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

PUBLIC_KEY = "bW9jay1wdWJsaWMta2V5"
PAYLOAD_HASH = f"sha256:{'a' * 64}"


def mock_signature(public_key: str, payload_hash: str) -> str:
    digest = hashlib.sha256(f"{public_key}:{payload_hash}".encode("utf-8")).digest()
    return base64.b64encode(digest).decode("ascii")


def create_subject() -> dict:
    response = client.post(
        "/api/v1/identity/subjects",
        json={
            "name": "验签主体",
            "type": "operator",
            "publicKey": PUBLIC_KEY,
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


def test_verify_registered_subject_with_valid_mock_signature() -> None:
    subject = create_subject()

    response = client.post(
        "/api/v1/identity/verify",
        json={
            "subjectDid": subject["subjectDid"],
            "signature": mock_signature(PUBLIC_KEY, PAYLOAD_HASH),
            "payloadHash": PAYLOAD_HASH,
        },
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "valid": True,
        "did": subject["subjectDid"],
        "subjectType": "operator",
    }


def test_verify_rejects_unknown_did() -> None:
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


def test_verify_rejects_invalid_signature() -> None:
    subject = create_subject()

    response = client.post(
        "/api/v1/identity/verify",
        json={
            "subjectDid": subject["subjectDid"],
            "signature": "aW52YWxpZC1zaWduYXR1cmU=",
            "payloadHash": PAYLOAD_HASH,
        },
    )

    assert response.status_code == 401
    assert response.json()["code"] == 40103
    assert response.json()["message"] == "invalid signature"


def test_verify_rejects_malformed_payload_hash() -> None:
    subject = create_subject()

    response = client.post(
        "/api/v1/identity/verify",
        json={
            "subjectDid": subject["subjectDid"],
            "signature": "aW52YWxpZA==",
            "payloadHash": "sha256:not-hex",
        },
    )

    assert response.status_code == 401
    assert response.json()["code"] == 40104
    assert response.json()["message"] == "invalid hash"
