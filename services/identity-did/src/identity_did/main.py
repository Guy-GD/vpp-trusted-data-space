from fastapi import FastAPI

import vpp_common

from .api import build_router
from .repository import InMemoryRepository
from .service import Clock


def create_app(
    repository: InMemoryRepository | None = None,
    clock: Clock | None = None,
) -> FastAPI:
    active_repository = repository if repository is not None else InMemoryRepository()
    application = FastAPI(
        title="VPP Identity DID Mock",
        version="0.1.0",
    )
    vpp_common.install_exception_handlers(application)
    application.include_router(build_router(active_repository, clock))
    return application


app = create_app()
