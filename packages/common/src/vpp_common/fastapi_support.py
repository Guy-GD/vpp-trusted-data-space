from collections.abc import Sequence

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .errors import ERROR_MESSAGES, ErrorCode, http_status_for
from .response import failure
from .schemas import ErrorDetail
from .tracing import (
    TRACE_HEADER,
    reset_current_trace_id,
    resolve_trace_id,
    set_current_trace_id,
)


class ServiceError(Exception):
    def __init__(
        self,
        code: ErrorCode | int,
        *,
        message: str | None = None,
        details: Sequence[ErrorDetail] | None = None,
    ) -> None:
        self.code = ErrorCode(code)
        self.message = message or ERROR_MESSAGES[self.code]
        self.details = list(details) if details else None
        super().__init__(self.message)


def _json_error(
    code: ErrorCode,
    trace_id: str,
    *,
    message: str | None = None,
    details: list[ErrorDetail] | None = None,
) -> JSONResponse:
    body = failure(
        code,
        trace_id=trace_id,
        message=message,
        details=details,
    )
    return JSONResponse(
        status_code=http_status_for(code),
        content=body.model_dump(exclude={"details"} if details is None else set()),
        headers={TRACE_HEADER: trace_id},
    )


def install_exception_handlers(app: FastAPI) -> None:
    """Install the frozen trace middleware and unified exception handlers."""

    @app.middleware("http")
    async def trace_middleware(request: Request, call_next):
        trace_id = resolve_trace_id(request.headers.get(TRACE_HEADER))
        request.state.trace_id = trace_id
        token = set_current_trace_id(trace_id)
        try:
            response = await call_next(request)
            response.headers[TRACE_HEADER] = trace_id
            return response
        finally:
            reset_current_trace_id(token)

    @app.exception_handler(ServiceError)
    async def service_error_handler(request: Request, exc: ServiceError):
        return _json_error(
            exc.code,
            request.state.trace_id,
            message=exc.message,
            details=exc.details,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        details = [
            ErrorDetail(
                field=".".join(str(item) for item in error["loc"] if item != "body"),
                reason=error["msg"],
            )
            for error in exc.errors()
        ]
        return _json_error(
            ErrorCode.INVALID_REQUEST,
            request.state.trace_id,
            details=details,
        )

    @app.exception_handler(Exception)
    async def internal_error_handler(request: Request, exc: Exception):
        return _json_error(ErrorCode.INTERNAL_ERROR, request.state.trace_id)
