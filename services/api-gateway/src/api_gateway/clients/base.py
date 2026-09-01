import httpx

from vpp_common import ErrorCode, ServiceError

CALLER_DID = "did:vpp:operator:001"


class BaseClient:
    """
    真实下游 HTTP 客户端基类。

    错误映射（契约冻结）：
      TimeoutException    -> 50401 DOWNSTREAM_TIMEOUT
      ConnectError/HTTP   -> 50203 DOWNSTREAM_UNAVAILABLE
      非统一响应           -> 50202 DOWNSTREAM_INVALID_RESPONSE
      下游非零 code        -> 保留可识别错误码，否则 50201
    """

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 5.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            transport=transport,
        )

    async def post(
        self,
        path: str,
        trace_id: str,
        payload: dict | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> dict:
        headers = {
            "X-Trace-Id": trace_id,
            "X-Caller-Did": CALLER_DID,
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        try:
            response = await self._client.post(
                path,
                json=payload or {},
                headers=headers,
            )
        except httpx.TimeoutException as exc:
            raise ServiceError(ErrorCode.DOWNSTREAM_TIMEOUT) from exc
        except httpx.HTTPError as exc:
            raise ServiceError(ErrorCode.DOWNSTREAM_UNAVAILABLE) from exc

        try:
            body = response.json()
        except ValueError as exc:
            raise ServiceError(ErrorCode.DOWNSTREAM_INVALID_RESPONSE) from exc

        if not isinstance(body, dict) or "code" not in body:
            raise ServiceError(ErrorCode.DOWNSTREAM_INVALID_RESPONSE)

        if body.get("code") != 0:
            code = body.get("code")
            try:
                error_code = ErrorCode(code)
            except ValueError:
                error_code = ErrorCode.DOWNSTREAM_REJECTED
            raise ServiceError(error_code)

        return body.get("data")