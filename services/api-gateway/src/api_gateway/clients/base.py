from typing import Any
import asyncio


class BaseMockClient:
    """
    下游服务模拟客户端基类
    """

    def __init__(
        self,
        service_name: str,
        timeout: float = 5.0,
    ):
        self.service_name = service_name
        self.timeout = timeout


    async def request(
        self,
        action: str,
        payload: dict | None = None,
    ) -> dict[str, Any]:

        if payload is None:
            payload = {}


        # 模拟网络延迟
        await asyncio.sleep(0.01)


        return {
            "service": self.service_name,
            "action": action,
            "status": "SUCCESS",
            "data": payload,
        }