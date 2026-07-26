from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from vpp_common import new_id
from vpp_common.errors import ErrorCode
from vpp_common.fastapi_support import ServiceError

from .repository import repo
from .schemas import AssetData, CreateAssetRequest, DataIngestRequest, IngestData, ReadingItem


def _verify_did(did: str, field: str = "ownerDid") -> None:
    """Mock DID validation — must start with 'did:vpp:'."""
    if not did.startswith("did:vpp:"):
        raise ServiceError(
            ErrorCode.INVALID_DID,
            details=[{"field": field, "reason": "must start with did:vpp:"}],
        )


def _verify_hash(reading: ReadingItem, field: str = "hash") -> None:
    """Mock hash validation — recompute sha256(ciphertext + '|' + timestamp) and compare."""
    raw = f"{reading.ciphertext}|{reading.timestamp.isoformat()}"
    recomputed = "sha256:" + hashlib.sha256(raw.encode()).hexdigest()
    if recomputed != reading.hash:
        raise ServiceError(
            ErrorCode.INVALID_HASH,
            details=[{"field": field, "reason": "hash does not match recomputed sha256(ciphertext|timestamp)"}],
        )


def _verify_signature(reading: ReadingItem, field: str = "signature") -> None:
    """Mock signature validation — signature must equal 'sig:' + hash."""
    expected = "sig:" + reading.hash
    if reading.signature != expected:
        raise ServiceError(
            ErrorCode.INVALID_SIGNATURE,
            details=[{"field": field, "reason": "signature must equal sig: + hash"}],
        )


def ingest(request: DataIngestRequest) -> IngestData:
    """Main-flow: verify each reading's signature & hash, then register asset."""
    _verify_did(request.ownerDid, "ownerDid")

    if not request.readings:
        raise ServiceError(
            ErrorCode.INVALID_REQUEST,
            details=[{"field": "readings", "reason": "readings must not be empty"}],
        )

    for i, reading in enumerate(request.readings):
        _verify_hash(reading, f"readings.{i}.hash")
        _verify_signature(reading, f"readings.{i}.signature")

    asset_id = new_id("asset_")
    result = IngestData(
        assetId=asset_id,
        readingBatchId=request.readingBatchId,
        ownerDid=request.ownerDid,
        assetType="meter_readings",
        sensitivityLevel="private",
        status="registered",
    )

    full_asset = AssetData(
        assetId=asset_id,
        readingBatchId=request.readingBatchId,
        ownerDid=request.ownerDid,
        assetType="meter_readings",
        sensitivityLevel="private",
        status="registered",
        createdAt=datetime.now(timezone.utc),
    )
    repo.save_asset(full_asset)
    return result


def create_asset(request: CreateAssetRequest) -> AssetData:
    """Standalone asset registration (not part of main demo flow)."""
    _verify_did(request.ownerDid, "ownerDid")

    asset_id = new_id("asset_")
    asset = AssetData(
        assetId=asset_id,
        readingBatchId=request.readingBatchId,
        ownerDid=request.ownerDid,
        assetType=request.assetType,
        sensitivityLevel=request.sensitivityLevel,
        status="registered",
        purpose=request.purpose,
        createdAt=datetime.now(timezone.utc),
    )
    repo.save_asset(asset)
    return asset


def get_asset(asset_id: str) -> AssetData:
    """Query asset metadata by ID."""
    asset = repo.get_asset(asset_id)
    if asset is None:
        raise ServiceError(
            ErrorCode.RESOURCE_NOT_FOUND,
            details=[{"field": "assetId", "reason": f"asset not found: {asset_id}"}],
        )
    return asset
