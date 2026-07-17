from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from .errors import ERROR_MESSAGES, ErrorCode
from .schemas import ErrorDetail
from .time_utils import utc_now_iso
from .tracing import resolve_trace_id


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")

    code: int
    message: str
    data: T | None
    traceId: str
    timestamp: str = Field(default_factory=utc_now_iso)
    details: list[ErrorDetail] | None = None


def success(
    data: T | None = None,
    *,
    trace_id: str | None = None,
    message: str = "ok",
) -> ApiResponse[T]:
    return ApiResponse(
        code=0,
        message=message,
        data=data,
        traceId=resolve_trace_id(trace_id),
    )


def failure(
    code: ErrorCode | int,
    *,
    trace_id: str | None = None,
    message: str | None = None,
    details: list[ErrorDetail] | None = None,
) -> ApiResponse[None]:
    error_code = ErrorCode(code)
    return ApiResponse(
        code=int(error_code),
        message=message or ERROR_MESSAGES[error_code],
        data=None,
        traceId=resolve_trace_id(trace_id),
        details=details,
    )
