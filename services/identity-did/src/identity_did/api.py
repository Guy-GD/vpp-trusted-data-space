from typing import Annotated

from fastapi import APIRouter, Header

import vpp_common
from vpp_common import ErrorCode, ServiceError
from vpp_common.schemas import HealthData

from .repository import InMemoryRepository
from .schemas import (
    AuthorizationCreateRequest,
    DeviceCreateRequest,
    IdentityVerifyRequest,
    SubjectCreateRequest,
)
from .service import (
    AuthorizationService,
    Clock,
    IdempotencyService,
    IdentityService,
    SystemClock,
)


def normalize_idempotency_key(key: str | None) -> str | None:
    if key is None:
        return None
    normalized = key.strip()
    if not normalized:
        raise ServiceError(ErrorCode.INVALID_REQUEST)
    return normalized


def build_router(
    repository: InMemoryRepository,
    clock: Clock | None = None,
) -> APIRouter:
    router = APIRouter()
    service = IdentityService(repository)
    idempotency = IdempotencyService(repository)
    active_clock = clock if clock is not None else SystemClock()
    authorization = AuthorizationService(repository, active_clock)

    @router.get("/health")
    def health():
        return vpp_common.success(
            HealthData(service="identity-did", status="healthy")
        )

    @router.post("/api/v1/identity/subjects")
    def register_subject(
        request: SubjectCreateRequest,
        idempotency_key: Annotated[
            str | None,
            Header(alias="Idempotency-Key"),
        ] = None,
    ):
        data = idempotency.execute(
            normalize_idempotency_key(idempotency_key),
            "identity.subjects.create",
            request.model_dump(mode="json", by_alias=True),
            lambda: service.register_subject(request),
        )
        return vpp_common.success(data)

    @router.post("/api/v1/identity/devices")
    def register_device(
        request: DeviceCreateRequest,
        idempotency_key: Annotated[
            str | None,
            Header(alias="Idempotency-Key"),
        ] = None,
    ):
        data = idempotency.execute(
            normalize_idempotency_key(idempotency_key),
            "identity.devices.create",
            request.model_dump(mode="json", by_alias=True),
            lambda: service.register_device(request),
        )
        return vpp_common.success(data)

    @router.post("/api/v1/identity/verify")
    def verify_identity(
        request: IdentityVerifyRequest,
        idempotency_key: Annotated[
            str | None,
            Header(alias="Idempotency-Key"),
        ] = None,
    ):
        data = idempotency.execute(
            normalize_idempotency_key(idempotency_key),
            "identity.verify",
            request.model_dump(mode="json", by_alias=True),
            lambda: service.verify_identity(request),
        )
        return vpp_common.success(data)

    @router.post("/api/v1/auth/requests")
    def create_authorization(
        request: AuthorizationCreateRequest,
        idempotency_key: Annotated[
            str | None,
            Header(alias="Idempotency-Key"),
        ] = None,
        caller_did: Annotated[
            str | None,
            Header(alias="X-Caller-Did"),
        ] = None,
    ):
        authorization.require_matching_caller(
            caller_did,
            request.requester_did,
        )
        data = idempotency.execute(
            normalize_idempotency_key(idempotency_key),
            "create-authorization",
            request.model_dump(mode="json", by_alias=True),
            lambda: authorization.create_authorization(request),
        )
        return vpp_common.success(data)

    return router
