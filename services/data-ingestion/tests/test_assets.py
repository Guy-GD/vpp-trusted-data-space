import pytest
from fastapi.testclient import TestClient

from data_ingestion.main import app

client = TestClient(app)

VALID_ASSET_BODY = {
    "readingBatchId": "batch_001",
    "ownerDid": "did:vpp:load-aggregator:001",
    "assetType": "meter_readings",
    "sensitivityLevel": "private",
    "purpose": "federated_training",
}


class TestAssetCreate:
    def test_create_asset_returns_asset(self):
        resp = client.post("/api/v1/data/assets", json=VALID_ASSET_BODY)
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        data = body["data"]
        assert data["assetId"].startswith("asset_")
        assert data["status"] == "registered"
        assert data["createdAt"] is not None

    def test_create_asset_idempotency_same_key_returns_cached(self):
        headers = {"Idempotency-Key": "asset-key-001"}
        r1 = client.post("/api/v1/data/assets", json=VALID_ASSET_BODY, headers=headers)
        r2 = client.post("/api/v1/data/assets", json=VALID_ASSET_BODY, headers=headers)
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["data"]["assetId"] == r2.json()["data"]["assetId"]

    def test_create_asset_invalid_did_returns_401(self):
        body = {**VALID_ASSET_BODY, "ownerDid": "bad_did"}
        resp = client.post("/api/v1/data/assets", json=body)
        assert resp.status_code == 401
        assert resp.json()["code"] == 40102

    def test_create_asset_missing_field_returns_400(self):
        resp = client.post("/api/v1/data/assets", json={})
        assert resp.status_code == 400
        assert resp.json()["code"] == 40001


class TestAssetQuery:
    def test_query_existing_asset(self):
        # first create one
        r = client.post("/api/v1/data/assets", json=VALID_ASSET_BODY)
        asset_id = r.json()["data"]["assetId"]

        resp = client.get(f"/api/v1/data/assets/{asset_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["assetId"] == asset_id
        assert body["data"]["status"] == "registered"

    def test_query_nonexistent_asset_returns_404(self):
        resp = client.get("/api/v1/data/assets/asset_nonexistent")
        assert resp.status_code == 404
        assert resp.json()["code"] == 40401
