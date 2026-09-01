from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReadingItem(BaseModel):
    """A single encrypted meter reading."""

    readingId: str
    meterId: str
    ciphertext: str
    signature: str
    hash: str
    timestamp: datetime


class DataIngestRequest(BaseModel):
    """POST /api/v1/data/ingest — main-flow batch with readings."""

    readingBatchId: str
    ownerDid: str
    readings: list[ReadingItem]


class CreateAssetRequest(BaseModel):
    """POST /api/v1/data/assets — standalone asset metadata registration."""

    readingBatchId: str
    ownerDid: str
    assetType: str
    sensitivityLevel: str
    purpose: str


class AssetData(BaseModel):
    """Asset metadata returned by ingest, create, and query."""

    assetId: str
    readingBatchId: str
    ownerDid: str
    assetType: str
    sensitivityLevel: str
    status: str
    purpose: Optional[str] = None
    createdAt: Optional[datetime] = None


class IngestData(BaseModel):
    """Data returned specifically by the ingest endpoint."""

    assetId: str
    readingBatchId: str
    ownerDid: str
    assetType: str
    sensitivityLevel: str
    status: str
