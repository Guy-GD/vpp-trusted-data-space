import hashlib
import json

from fastapi import APIRouter, Header, Request

from vpp_common import ErrorCode, ServiceError, success

from .schemas import DemoRequest, HealthData
from .repository import repository
from .workflows.demo import DemoWorkflow
from .idempotency import idempotency_service


router = APIRouter(prefix="/api/v1")

workflow = DemoWorkflow()


def _request_hash(payload: dict) -> str:
    content = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()


@router.get("/health")
async def health(request: Request):
    return success(
        HealthData(service="api-gateway", status="healthy"),
        trace_id=request.state.trace_id,
    )


@router.post("/demo/run")
async def run_demo(
    demo_request: DemoRequest,
    request: Request,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
    ),
):
    trace_id = request.state.trace_id
    fingerprint = _request_hash(demo_request.model_dump())

    # ---- 幂等检查：同 key 同请求体 -> 返回旧结果；同 key 异请求体 -> 40901 ----
    if idempotency_key:
        old_result = idempotency_service.check(idempotency_key, fingerprint)
        if old_result is not None:
            return success(old_result, trace_id=trace_id)

    result = await workflow.run(demo_request, trace_id)
    response_data = result.model_dump()

    if idempotency_key:
        idempotency_service.save(idempotency_key, fingerprint, response_data)

    return success(response_data, trace_id=trace_id)


@router.get("/demo/status/{business_id}")
async def demo_status(business_id: str, request: Request):
    state = repository.get(business_id)
    if state is None:
        raise ServiceError(ErrorCode.BUSINESS_NOT_FOUND)
    return success(state.model_dump(), trace_id=request.state.trace_id)