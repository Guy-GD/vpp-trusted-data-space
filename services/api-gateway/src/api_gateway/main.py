from fastapi import FastAPI

from .api import router
from .middleware.trace import TraceMiddleware


def create_app() -> FastAPI:

    app = FastAPI(
        title="VPP Trusted Data Space Gateway",
        version="0.1.0",
    )

    # 注册 TraceId 中间件
    app.add_middleware(
        TraceMiddleware
    )

    # 注册 API 路由
    app.include_router(router)

    return app


app = create_app()