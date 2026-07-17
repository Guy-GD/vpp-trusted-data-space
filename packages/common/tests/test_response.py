from datetime import datetime
from inspect import signature

import pytest

from vpp_common.errors import ERROR_MESSAGES, ErrorCode, http_status_for
from vpp_common.fastapi_support import ServiceError
from vpp_common.response import failure, success
from vpp_common.schemas import ErrorDetail


EXPECTED_ERROR_CODES = {
    40001,
    40002,
    40003,
    40004,
    40005,
    40101,
    40102,
    40103,
    40104,
    40301,
    40302,
    40303,
    40401,
    40402,
    40403,
    40404,
    40901,
    40902,
    40903,
    42201,
    42202,
    42203,
    42204,
    42901,
    50001,
    50002,
    50003,
    50201,
    50202,
    50203,
    50301,
    50302,
    50303,
    50401,
}


def test_success_builds_unified_envelope():
    response = success({"assetId": "asset_001"}, trace_id="trace_existing")

    assert response.code == 0
    assert response.message == "ok"
    assert response.data == {"assetId": "asset_001"}
    assert response.traceId == "trace_existing"
    assert response.details is None
    assert datetime.fromisoformat(response.timestamp.replace("Z", "+00:00")).tzinfo is not None


def test_failure_uses_catalog_message_and_details():
    response = failure(
        ErrorCode.INVALID_REQUEST,
        trace_id="trace_existing",
        details=[ErrorDetail(field="participants", reason="must not be empty")],
    )

    assert response.code == 40001
    assert response.message == "invalid request"
    assert response.data is None
    assert response.traceId == "trace_existing"
    assert response.details == [
        ErrorDetail(field="participants", reason="must not be empty")
    ]


def test_response_builders_and_service_error_do_not_expose_message_override():
    assert "message" not in signature(success).parameters
    assert "message" not in signature(failure).parameters
    assert "message" not in signature(ServiceError).parameters

    with pytest.raises(TypeError):
        success({}, message="caller controlled")
    with pytest.raises(TypeError):
        failure(ErrorCode.INVALID_REQUEST, message="caller controlled")
    with pytest.raises(TypeError):
        ServiceError(ErrorCode.INVALID_REQUEST, message="caller controlled")


def test_every_error_code_has_one_stable_catalog_message():
    assert len(set(ERROR_MESSAGES.values())) == len(ERROR_MESSAGES)
    for code, message in ERROR_MESSAGES.items():
        assert failure(code, trace_id="trace_existing").message == message


def test_error_catalog_matches_frozen_document():
    assert {int(code) for code in ErrorCode} == EXPECTED_ERROR_CODES
    assert set(ERROR_MESSAGES) == {ErrorCode(value) for value in EXPECTED_ERROR_CODES}


def test_error_code_prefix_maps_to_http_status():
    assert http_status_for(ErrorCode.INVALID_REQUEST) == 400
    assert http_status_for(ErrorCode.INVALID_DID) == 401
    assert http_status_for(ErrorCode.ACCESS_DENIED) == 403
    assert http_status_for(ErrorCode.RESOURCE_NOT_FOUND) == 404
    assert http_status_for(ErrorCode.IDEMPOTENCY_CONFLICT) == 409
    assert http_status_for(ErrorCode.INSUFFICIENT_UPDATES) == 422
    assert http_status_for(ErrorCode.RATE_LIMIT_EXCEEDED) == 429
    assert http_status_for(ErrorCode.INTERNAL_ERROR) == 500
    assert http_status_for(ErrorCode.DOWNSTREAM_UNAVAILABLE) == 502
    assert http_status_for(ErrorCode.SERVICE_UNAVAILABLE) == 503
    assert http_status_for(ErrorCode.DOWNSTREAM_TIMEOUT) == 504
