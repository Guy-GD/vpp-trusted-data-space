from typing import Annotated

from fastapi import APIRouter, Header

import vpp_common
from vpp_common.schemas import HealthData

from .repository import InMemoryRepository
from .schemas import (
    DeviceCreateRequest,
    IdentityVerifyRequest,
    SubjectCreateRequest,
)
from .service import IdempotencyService, IdentityService


def build_router(repository: InMemoryRepository) -> APIRouter:
    router = APIRouter()
    service = IdentityService(repository)
    idempotency = IdempotencyService(repository)

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
            idempotency_key,
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
            idempotency_key,
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
            idempotency_key,
            "identity.verify",
            request.model_dump(mode="json", by_alias=True),
            lambda: service.verify_identity(request),
        )
        return vpp_common.success(data)

    return router
