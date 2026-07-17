import re
from contextvars import ContextVar, Token

from .id_generator import new_id


TRACE_HEADER = "X-Trace-Id"
MAX_TRACE_ID_LENGTH = 128
_TRACE_PATTERN = re.compile(r"^trace_[A-Za-z0-9._:-]*$")
_current_trace_id: ContextVar[str | None] = ContextVar(
    "vpp_trace_id", default=None
)


def _is_valid_trace_id(value: str) -> bool:
    return len(value) <= MAX_TRACE_ID_LENGTH and _TRACE_PATTERN.fullmatch(value) is not None


def resolve_trace_id(incoming: str | None = None) -> str:
    """Preserve a valid incoming trace ID or generate a safe replacement."""
    candidate = incoming or _current_trace_id.get()
    if candidate and _is_valid_trace_id(candidate):
        return candidate
    return new_id("trace_")


def set_current_trace_id(trace_id: str) -> Token[str | None]:
    return _current_trace_id.set(trace_id)


def reset_current_trace_id(token: Token[str | None]) -> None:
    _current_trace_id.reset(token)
