from uuid import uuid4

from fastapi import (
    APIRouter,
    Header,
    HTTPException,
    Request,
)

from .schemas import DemoRequest
from .repository import repository
from .workflows.demo import DemoWorkflow
from .audit import audit_repository
from .idempotency import idempotency_service


router = APIRouter(
    prefix="/api/v1"
)


workflow = DemoWorkflow()


@router.get("/health")
async def health(
    request: Request,
):

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "service": "api-gateway",
            "status": "healthy",
        },
        "traceId": request.state.trace_id,
    }



@router.post("/demo/run")
async def run_demo(
    demo_request: DemoRequest,
    request: Request,
    x_trace_id: str | None = Header(
        default=None
    ),
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key"
    ),
):

    trace_id = (
        x_trace_id
        or request.state.trace_id
        or str(uuid4())
    )


    # =========================
    # 幂等检查
    # =========================

    if idempotency_key:

        old_result = (
            idempotency_service.check(
                idempotency_key
            )
        )


        if old_result:

            return {
                "code": 0,
                "message": "ok",
                "data": old_result,
                "traceId": trace_id,
            }



    # =========================
    # 执行Demo工作流
    # =========================

    result = await workflow.run(
        demo_request,
        trace_id,
    )


    response_data = (
        result.model_dump()
    )



    # =========================
    # 保存幂等结果
    # =========================

    if idempotency_key:

        idempotency_service.save(
            idempotency_key,
            response_data,
        )



    return {
        "code": 0,
        "message": "ok",
        "data": response_data,
        "traceId": trace_id,
    }




@router.get(
    "/demo/status/{business_id}"
)
async def demo_status(
    business_id: str,
):

    state = repository.get(
        business_id
    )


    if state is None:

        raise HTTPException(
            status_code=404,
            detail={
                "message":
                "businessId not found"
            },
        )



    return {
        "code": 0,
        "message": "ok",
        "data": state.model_dump(),
        "traceId": getattr(
            state,
            "trace_id",
            None
        ),
    }




@router.get(
    "/demo/audit/{business_id}"
)
async def get_audit(
    business_id: str,
):

    events = (
        audit_repository
        .list_by_business(
            business_id
        )
    )


    return {
        "code": 0,
        "message": "ok",
        "data": {
            "businessId": business_id,
            "auditTrail": [
                event.model_dump()
                for event in events
            ]
        }
    }




@router.get(
    "/demo/audit/verify/{business_id}"
)
async def verify_audit(
    business_id: str,
):

    valid = (
        audit_repository
        .verify_chain(
            business_id
        )
    )


    events = (
        audit_repository
        .list_by_business(
            business_id
        )
    )


    return {
        "code": 0,
        "message": "ok",
        "data": {
            "businessId": business_id,
            "valid": valid,
            "eventCount": len(events),
            "message":
                (
                    "audit chain verified"
                    if valid
                    else
                    "audit chain invalid"
                ),
        }
    }