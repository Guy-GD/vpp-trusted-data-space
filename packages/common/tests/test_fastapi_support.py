import pytest
from fastapi import FastAPI, HTTPException
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

    @app.get("/http-not-found")
    def http_not_found():
        raise HTTPException(status_code=404, detail="secret HTTP exception detail")

    @app.get("/http-error/{status_code}")
    def http_error(status_code: int):
        raise HTTPException(
            status_code=status_code,
            detail=f"secret HTTP {status_code} detail",
        )

    @app.get("/http-unauthorized")
    def http_unauthorized():
        raise HTTPException(
            status_code=401,
            detail="secret authentication detail",
            headers={
                "www-authenticate": 'Bearer realm="vpp"',
                "Set-Cookie": "session=secret",
                "X-Internal-Debug": "secret-debug-value",
            },
        )

    @app.get("/http-rate-limited")
    def http_rate_limited():
        raise HTTPException(
            status_code=429,
            detail="secret limiter detail",
            headers={
                "rEtRy-AfTeR": "60",
                "X-Custom-Rate-Policy": "internal-policy",
            },
        )

    return app


def test_trace_id_is_preserved_in_body_and_header():
    client = TestClient(build_app())
    response = client.get("/ok", headers={"X-Trace-Id": "trace_existing"})

    assert response.status_code == 200
    assert response.json()["traceId"] == "trace_existing"
    assert response.headers["X-Trace-Id"] == "trace_existing"


def test_success_http_json_has_exact_public_keys():
    response = TestClient(build_app()).get("/ok")

    assert response.status_code == 200
    assert set(response.json()) == {
        "code",
        "message",
        "data",
        "traceId",
        "timestamp",
    }


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
    assert set(response.json()) == {
        "code",
        "message",
        "data",
        "traceId",
        "timestamp",
        "details",
    }


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


def test_http_not_found_is_normalized_without_detail_leakage():
    client = TestClient(build_app())
    response = client.get(
        "/http-not-found", headers={"X-Trace-Id": "trace_existing"}
    )

    assert response.status_code == 404
    assert response.json()["code"] == 40401
    assert response.json()["data"] is None
    assert response.json()["traceId"] == "trace_existing"
    assert response.headers["X-Trace-Id"] == "trace_existing"
    assert set(response.json()) == {
        "code",
        "message",
        "data",
        "traceId",
        "timestamp",
    }
    assert "secret HTTP exception detail" not in response.text


@pytest.mark.parametrize(
    ("status_code", "business_code"),
    [
        (400, 40001),
        (401, 40101),
        (403, 40301),
        (404, 40401),
        (409, 40901),
        (418, 40001),
        (422, 42201),
        (429, 42901),
        (500, 50001),
        (501, 50001),
        (502, 50201),
        (503, 50301),
        (504, 50401),
    ],
)
def test_http_exception_preserves_status_and_uses_frozen_business_code(
    status_code: int, business_code: int
):
    response = TestClient(build_app()).get(f"/http-error/{status_code}")

    assert response.status_code == status_code
    assert response.json()["code"] == business_code
    assert response.json()["data"] is None
    assert "details" not in response.json()
    assert f"secret HTTP {status_code} detail" not in response.text


def test_real_http_401_preserves_auth_header_and_filters_other_headers():
    response = TestClient(build_app()).get(
        "/http-unauthorized", headers={"X-Trace-Id": "trace_auth"}
    )

    assert response.status_code == 401
    assert response.json()["code"] == 40101
    assert response.json()["message"] == "missing identity"
    assert response.json()["traceId"] == "trace_auth"
    assert response.headers["X-Trace-Id"] == "trace_auth"
    assert response.headers["WWW-Authenticate"] == 'Bearer realm="vpp"'
    assert "set-cookie" not in response.headers
    assert "x-internal-debug" not in response.headers
    assert "secret authentication detail" not in response.text


def test_real_router_http_405_preserves_status_allow_and_trace_id():
    response = TestClient(build_app()).post(
        "/ok", headers={"X-Trace-Id": "trace_method"}
    )

    assert response.status_code == 405
    assert response.json()["code"] == 40001
    assert response.json()["message"] == "invalid request"
    assert response.json()["traceId"] == "trace_method"
    assert response.headers["X-Trace-Id"] == "trace_method"
    assert response.headers["Allow"] == "GET"
    assert "Method Not Allowed" not in response.text


def test_real_http_429_preserves_retry_after_and_filters_custom_headers():
    response = TestClient(build_app()).get(
        "/http-rate-limited", headers={"X-Trace-Id": "trace_rate"}
    )

    assert response.status_code == 429
    assert response.json()["code"] == 42901
    assert response.json()["message"] == "rate limit exceeded"
    assert response.json()["traceId"] == "trace_rate"
    assert response.headers["X-Trace-Id"] == "trace_rate"
    assert response.headers["Retry-After"] == "60"
    assert "x-custom-rate-policy" not in response.headers
    assert "secret limiter detail" not in response.text
