from fastapi import APIRouter

import vpp_common
from vpp_common.schemas import HealthData


def build_router() -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health():
        return vpp_common.success(
            HealthData(service="identity-did", status="healthy")
        )

    return router
