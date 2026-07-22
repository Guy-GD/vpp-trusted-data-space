from fastapi import FastAPI

import vpp_common

from .api import build_router


def create_app() -> FastAPI:
    application = FastAPI(
        title="VPP Identity DID Mock",
        version="0.1.0",
    )
    vpp_common.install_exception_handlers(application)
    application.include_router(build_router())
    return application


app = create_app()
