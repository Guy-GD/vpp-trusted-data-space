from fastapi import APIRouter

import vpp_common
from vpp_common.schemas import HealthData

from .repository import InMemoryRepository
from .schemas import DeviceCreateRequest, SubjectCreateRequest
from .service import IdentityService


def build_router(repository: InMemoryRepository) -> APIRouter:
    router = APIRouter()
    service = IdentityService(repository)

    @router.get("/health")
    def health():
        return vpp_common.success(
            HealthData(service="identity-did", status="healthy")
        )

    @router.post("/api/v1/identity/subjects")
    def register_subject(request: SubjectCreateRequest):
        return vpp_common.success(service.register_subject(request))

    @router.post("/api/v1/identity/devices")
    def register_device(request: DeviceCreateRequest):
        return vpp_common.success(service.register_device(request))

    return router
