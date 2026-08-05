from fastapi import FastAPI, Request
from vpp_common import install_exception_handlers

from .api import health_router, router

app = FastAPI(title="data-ingestion", version="0.1.0")
app.include_router(health_router)
app.include_router(router)

install_exception_handlers(app)


@app.middleware("http")
async def capture_body(request: Request, call_next):
    """Capture raw body dict once so routes don't re-read request.body()."""
    if request.method in ("POST", "PUT", "PATCH"):
        import json
        raw = await request.body()
        try:
            request.state.body_dict = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError):
            request.state.body_dict = None
    response = await call_next(request)
    return response
