from .base import BaseClient
from ..settings import get_settings


class MeterClient(BaseClient):
    def __init__(self, *, transport=None):
        settings = get_settings()
        super().__init__(
            settings.meter_service_url,
            timeout=settings.http_timeout_seconds,
            transport=transport,
        )

    async def collect_readings(self, meter_count: int, trace_id: str) -> dict:
        return await self.post(
            "/api/v1/meter/readings/generate",
            trace_id,
            {"meterCount": meter_count},
        )