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
    if not idempotency_key:
        result: IngestData = ingest(body)
        return success(result.model_dump(), trace_id=getattr(request.state, "trace_id", None))

    body_hash = repo._hash_body(request.state.body_dict)
    result: IngestData = repo.execute_idempotent(idempotency_key, body_hash, lambda: ingest(body))
    return success(result.model_dump(), trace_id=getattr(request.state, "trace_id", None))


# ---- POST /api/v1/data/assets -----------------------------------------------

@router.post("/data/assets")
async def data_assets(
    request: Request,
    body: CreateAssetRequest,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    if not idempotency_key:
        result: AssetData = create_asset(body)
        return success(result.model_dump(), trace_id=getattr(request.state, "trace_id", None))

    body_hash = repo._hash_body(request.state.body_dict)
    result: AssetData = repo.execute_idempotent(idempotency_key, body_hash, lambda: create_asset(body))
    return success(result.model_dump(), trace_id=getattr(request.state, "trace_id", None))


# ---- GET /api/v1/data/assets/{assetId} --------------------------------------

@router.get("/data/assets/{assetId}")
async def data_assets_query(request: Request, assetId: str):
    result = get_asset(assetId)
    return success(result.model_dump(), trace_id=getattr(request.state, "trace_id", None))

