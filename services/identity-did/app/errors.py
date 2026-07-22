from typing import Any


class ApiError(Exception):
    def __init__(self, http_status: int, code: int, message: str) -> None:
        super().__init__(message)
        self.http_status = http_status
        self.code = code
        self.message = message


def success_envelope(data: Any, trace_id: str, message: str = "ok") -> dict[str, Any]:
    return {
        "code": 0,
        "message": message,
        "data": data,
        "traceId": trace_id,
    }


def error_envelope(code: int, message: str, trace_id: str) -> dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "data": None,
        "traceId": trace_id,
    }
