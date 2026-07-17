from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from vpp_common.errors import ErrorCode
from vpp_common.fastapi_support import ServiceError, install_exception_handlers
from vpp_common.response import success
from vpp_common.schemas import ErrorDetail


class Payload(BaseModel):
    value: int


def build_app() -> FastAPI:
    app = FastAPI()
    install_exception_handlers(app)

    @app.get("/ok")
    def ok():
        return success({"status": "ready"})

    @app.get("/service-error")
    def service_error():
        raise ServiceError(
            ErrorCode.RESOURCE_NOT_FOUND,
            details=[ErrorDetail(field="assetId", reason="not found")],
        )

    @app.post("/validation-error")
    def validation_error(payload: Payload):
        return success(payload.model_dump())

    @app.get("/internal-error")
    def internal_error():
        raise RuntimeError("secret implementation detail")

    return app


def test_trace_id_is_preserved_in_body_and_header():
    client = TestClient(build_app())
    response = client.get("/ok", headers={"X-Trace-Id": "trace_existing"})

    assert response.status_code == 200
    assert response.json()["traceId"] == "trace_existing"
    assert response.headers["X-Trace-Id"] == "trace_existing"


def test_service_error_uses_unified_envelope():
    client = TestClient(build_app())
    response = client.get("/service-error")

    assert response.status_code == 404
    assert response.json()["code"] == 40401
    assert response.json()["data"] is None
    assert response.json()["details"] == [
        {"field": "assetId", "reason": "not found"}
    ]
    assert response.json()["traceId"].startswith("trace_")


def test_validation_error_is_normalized():
    client = TestClient(build_app())
    response = client.post("/validation-error", json={"value": "wrong"})

    assert response.status_code == 400
    assert response.json()["code"] == 40001
    assert response.json()["message"] == "invalid request"
    assert response.json()["details"]


def test_internal_error_does_not_leak_exception_message():
    client = TestClient(build_app(), raise_server_exceptions=False)
    response = client.get("/internal-error")

    assert response.status_code == 500
    assert response.json()["code"] == 50001
    assert response.json()["message"] == "internal error"
    assert "secret implementation detail" not in response.text
