import json

import pytest
from fastapi.testclient import TestClient

from data_ingestion.main import app

client = TestClient(app)

VALID_BODY = {
    "readingBatchId": "batch_001",
    "ownerDid": "did:vpp:load-aggregator:001",
    "readings": [
        {
            "readingId": "reading_001",
            "meterId": "meter_001",
            "ciphertext": "dGVzdC1jaXBoZXJ0ZXh0LTAwMQ==",
            "signature": "sig:sha256:96aa04d3c0077c851035c056b292f9f874891d8be5ffcbec16dfae3033019054",
            "hash": "sha256:96aa04d3c0077c851035c056b292f9f874891d8be5ffcbec16dfae3033019054",
            "timestamp": "2026-07-22T10:00:00+08:00",
        },
        {
            "readingId": "reading_002",
            "meterId": "meter_002",
            "ciphertext": "dGVzdC1jaXBoZXJ0ZXh0LTAwMg==",
            "signature": "sig:sha256:4f91c5d39f568ef413ea559025021265ccee97118e96cb1a68401a72d336a79e",
            "hash": "sha256:4f91c5d39f568ef413ea559025021265ccee97118e96cb1a68401a72d336a79e",
            "timestamp": "2026-07-22T10:05:00+08:00",
        },
    ],
}


class TestIngestSuccess:
    def test_ingest_returns_asset(self):
        resp = client.post("/api/v1/data/ingest", json=VALID_BODY)
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        data = body["data"]
        assert data["assetId"].startswith("asset_")
        assert data["readingBatchId"] == "batch_001"
        assert data["ownerDid"] == "did:vpp:load-aggregator:001"
        assert data["assetType"] == "meter_readings"
        assert data["sensitivityLevel"] == "private"
        assert data["status"] == "registered"

    def test_ingest_idempotency_same_key_returns_cached(self):
        headers = {"Idempotency-Key": "ingest-key-001"}
        r1 = client.post("/api/v1/data/ingest", json=VALID_BODY, headers=headers)
        r2 = client.post("/api/v1/data/ingest", json=VALID_BODY, headers=headers)
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["data"]["assetId"] == r2.json()["data"]["assetId"]

    def test_ingest_with_trace_header(self):
        headers = {"X-Trace-Id": "trace_custom_001"}
        resp = client.post("/api/v1/data/ingest", json=VALID_BODY, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["traceId"] == "trace_custom_001"


class TestIngestFailures:
    def test_missing_field_returns_400(self):
        resp = client.post("/api/v1/data/ingest", json={})
        assert resp.status_code == 400
        assert resp.json()["code"] == 40001

    def test_empty_readings_returns_400(self):
        body = {**VALID_BODY, "readings": []}
        resp = client.post("/api/v1/data/ingest", json=body)
        assert resp.status_code == 400
        assert resp.json()["code"] == 40001

    def test_invalid_owner_did_returns_401(self):
        body = {**VALID_BODY, "ownerDid": "bad_did"}
        resp = client.post("/api/v1/data/ingest", json=body)
        assert resp.status_code == 401
        assert resp.json()["code"] == 40102

    def test_invalid_hash_returns_401(self):
        body = json.loads(json.dumps(VALID_BODY))
        body["readings"][0]["hash"] = "bad_hash"
        resp = client.post("/api/v1/data/ingest", json=body)
        assert resp.status_code == 401
        assert resp.json()["code"] == 40104

    def test_empty_signature_returns_401(self):
        body = json.loads(json.dumps(VALID_BODY))
        body["readings"][0]["signature"] = ""
        resp = client.post("/api/v1/data/ingest", json=body)
        assert resp.status_code == 401
        assert resp.json()["code"] == 40103

    def test_idempotency_conflict_returns_409(self):
        headers = {"Idempotency-Key": "ingest-conflict-001"}
        client.post("/api/v1/data/ingest", json=VALID_BODY, headers=headers)
        # same key, different body
        different = json.loads(json.dumps(VALID_BODY))
        different["readingBatchId"] = "batch_999"
        resp = client.post("/api/v1/data/ingest", json=different, headers=headers)
        assert resp.status_code == 409
        assert resp.json()["code"] == 40901
