from fastapi import FastAPI

from vpp_common import install_exception_handlers

from .api import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="VPP Trusted Data Space Gateway",
        version="0.1.0",
    )
    # 统一 trace 中间件 + 异常处理（来自 vpp_common）
    install_exception_handlers(app)
    app.include_router(router)
    return app


app = create_app()