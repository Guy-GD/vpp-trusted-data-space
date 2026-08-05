from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


TRACE_HEADER = "X-Trace-Id"


class TraceMiddleware(BaseHTTPMiddleware):
    """
    TraceId生成和透传中间件
    """

    async def dispatch(
        self,
        request: Request,
        call_next,
    ):

        trace_id = request.headers.get(
            TRACE_HEADER
        )

        if not trace_id:
            trace_id = str(uuid4())

        request.state.trace_id = trace_id

        response = await call_next(
            request
        )

        response.headers[
            TRACE_HEADER
        ] = trace_id

        return response