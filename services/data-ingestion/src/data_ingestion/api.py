from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, Request
from vpp_common import success

from .repository import repo
from .schemas import AssetData, CreateAssetRequest, DataIngestRequest, IngestData
from .service import create_asset, get_asset, ingest

# ---- routers ----------------------------------------------------------------

health_router = APIRouter(tags=["health"])
router = APIRouter(prefix="/api/v1", tags=["data-ingestion"])


# ---- health -----------------------------------------------------------------

@health_router.get("/health")
async def health(request: Request):
    return success(
        {"service": "data-ingestion", "status": "healthy"},
        trace_id=getattr(request.state, "trace_id", None),
    )


# ---- POST /api/v1/data/ingest -----------------------------------------------

@router.post("/data/ingest")
async def data_ingest(
    request: Request,
    body: DataIngestRequest,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    body_dict = await _body_dict(request)
    body_hash = repo._hash_body(body_dict)

    # idempotency check
    if idempotency_key:
        cached = repo.idempotency_check(idempotency_key, body_hash)
        if cached is not None:
            return success(cached.model_dump(), trace_id=getattr(request.state, "trace_id", None))

    result: IngestData = ingest(body)

    if idempotency_key:
        repo.idempotency_save(idempotency_key, body_hash, result)

    return success(result.model_dump(), trace_id=getattr(request.state, "trace_id", None))


# ---- POST /api/v1/data/assets -----------------------------------------------

@router.post("/data/assets")
async def data_assets(
    request: Request,
    body: CreateAssetRequest,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    body_dict = await _body_dict(request)
    body_hash = repo._hash_body(body_dict)

    if idempotency_key:
        cached = repo.idempotency_check(idempotency_key, body_hash)
        if cached is not None:
            return success(cached.model_dump(), trace_id=getattr(request.state, "trace_id", None))

    result: AssetData = create_asset(body)

    if idempotency_key:
        repo.idempotency_save(idempotency_key, body_hash, result)

    return success(result.model_dump(), trace_id=getattr(request.state, "trace_id", None))


# ---- GET /api/v1/data/assets/{assetId} --------------------------------------

@router.get("/data/assets/{assetId}")
async def data_assets_query(request: Request, assetId: str):
    result = get_asset(assetId)
    return success(result.model_dump(), trace_id=getattr(request.state, "trace_id", None))


# ---- helpers ----------------------------------------------------------------

async def _body_dict(request: Request) -> dict:
    """Re-read the raw body to get a plain dict for idempotency hashing."""
    raw = await request.body()
    import json

    return json.loads(raw)
