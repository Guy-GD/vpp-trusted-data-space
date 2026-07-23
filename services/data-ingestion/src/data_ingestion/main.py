from fastapi import FastAPI
from vpp_common import install_exception_handlers

from .api import health_router, router

app = FastAPI(title="data-ingestion", version="0.1.0")
app.include_router(health_router)
app.include_router(router)

install_exception_handlers(app)
