from uuid import uuid4

from fastapi import FastAPI, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.errors import ApiError, error_envelope, success_envelope
from app.models import (
    AuthorizationCreateRequest,
    AuthorizationDecisionRequest,
    DeviceCreateRequest,
    IdentityVerifyRequest,
    SubjectCreateRequest,
)
from app.service import (
    authorization_service,
    idempotency_service,
    identity_service,
    require_matching_caller,
)


app = FastAPI(
    title="VPP Identity DID Demo",
    version="0.1.0",
)


@app.middleware("http")
async def attach_trace_id(request: Request, call_next):
    request.state.trace_id = request.headers.get("X-Trace-Id") or f"trace_{uuid4().hex}"
    return await call_next(request)


@app.exception_handler(ApiError)
async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content=error_envelope(exc.code, exc.message, request.state.trace_id),
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    missing = any(error.get("type") == "missing" for error in exc.errors())
    code = 40002 if missing else 40001
    message = "missing required field" if missing else "invalid request"
    return JSONResponse(
        status_code=400,
        content=error_envelope(code, message, request.state.trace_id),
    )


@app.get("/health")
async def health(request: Request) -> dict:
    return success_envelope(
        data={
            "service": "identity-did",
            "status": "healthy",
        },
        trace_id=request.state.trace_id,
    )


@app.post("/api/v1/identity/subjects")
async def create_subject(
    payload: SubjectCreateRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict:
    return idempotency_service.execute(
        key=idempotency_key,
        operation="create-subject",
        payload=payload.model_dump(mode="json", by_alias=True),
        trace_id=request.state.trace_id,
        action=lambda: identity_service.register_subject(
            name=payload.name,
            subject_type=payload.type,
            public_key=payload.public_key,
        ),
    )


@app.post("/api/v1/identity/devices")
async def create_device(
    payload: DeviceCreateRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict:
    return idempotency_service.execute(
        key=idempotency_key,
        operation="create-device",
        payload=payload.model_dump(mode="json", by_alias=True),
        trace_id=request.state.trace_id,
        action=lambda: identity_service.register_device(
            device_name=payload.device_name,
            device_type=payload.device_type,
            owner_did=payload.owner_did,
            public_key=payload.public_key,
        ),
    )


@app.post("/api/v1/identity/verify")
async def verify_identity(payload: IdentityVerifyRequest, request: Request) -> dict:
    did = payload.subject_did or payload.device_did
    data = identity_service.verify_identity(
        did=did,
        signature=payload.signature,
        payload_hash=payload.payload_hash,
    )
    return success_envelope(data, request.state.trace_id)


@app.post("/api/v1/auth/requests")
async def create_authorization(
    payload: AuthorizationCreateRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    caller_did: str | None = Header(default=None, alias="X-Caller-Did"),
) -> dict:
    require_matching_caller(caller_did, payload.requester_did)
    return idempotency_service.execute(
        key=idempotency_key,
        operation="create-authorization",
        payload=payload.model_dump(mode="json", by_alias=True),
        trace_id=request.state.trace_id,
        action=lambda: authorization_service.create(
            requester_did=payload.requester_did,
            owner_did=payload.owner_did,
            asset_id=payload.asset_id,
            purpose=payload.purpose,
            expire_at=payload.expire_at,
        ),
    )


@app.post("/api/v1/auth/requests/{auth_id}/approve")
async def decide_authorization(
    auth_id: str,
    payload: AuthorizationDecisionRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    caller_did: str | None = Header(default=None, alias="X-Caller-Did"),
) -> dict:
    require_matching_caller(caller_did, payload.approver_did)
    return idempotency_service.execute(
        key=idempotency_key,
        operation=f"decide-authorization:{auth_id}",
        payload=payload.model_dump(mode="json", by_alias=True),
        trace_id=request.state.trace_id,
        action=lambda: authorization_service.decide(
            auth_id=auth_id,
            approver_did=payload.approver_did,
            decision=payload.decision,
            reason=payload.reason,
        ),
    )


@app.get("/api/v1/auth/requests/{auth_id}")
async def get_authorization(auth_id: str, request: Request) -> dict:
    data = authorization_service.get(auth_id)
    return success_envelope(data, request.state.trace_id)
