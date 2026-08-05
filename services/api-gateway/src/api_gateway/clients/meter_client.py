from .base import BaseClient


class MeterClient(BaseClient):

    async def collect_readings(
        self,
        trace_id: str,
        payload: dict,
    ):

        return await self.post(
            "/collect",
            payload,
            trace_id,
        )