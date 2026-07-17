from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_serializer

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

    @model_serializer(mode="wrap")
    def _serialize_without_empty_details(self, handler):
        serialized = handler(self)
        if serialized.get("details") is None:
            serialized.pop("details", None)
        return serialized


def success(
    data: T | None = None,
    *,
    trace_id: str | None = None,
) -> ApiResponse[T]:
    return ApiResponse(
        code=0,
        message="ok",
        data=data,
        traceId=resolve_trace_id(trace_id),
    )


def failure(
    code: ErrorCode | int,
    *,
    trace_id: str | None = None,
    details: list[ErrorDetail] | None = None,
) -> ApiResponse[None]:
    """Build an error envelope for exception handlers and non-HTTP use.

    FastAPI routes must raise ServiceError so the exception handler can apply
    the frozen non-200 HTTP status.
    """

    error_code = ErrorCode(code)
    return ApiResponse(
        code=int(error_code),
        message=ERROR_MESSAGES[error_code],
        data=None,
        traceId=resolve_trace_id(trace_id),
        details=details or None,
    )
