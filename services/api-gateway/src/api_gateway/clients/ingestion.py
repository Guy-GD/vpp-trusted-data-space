from .base import BaseClient
from ..settings import get_settings


class IngestionClient(BaseClient):
    def __init__(self, *, transport=None):
        settings = get_settings()
        super().__init__(
            settings.ingestion_service_url,
            timeout=settings.http_timeout_seconds,
            transport=transport,
        )

    async def register_asset(self, meter_data: dict, trace_id: str) -> dict:
        return await self.post(
            "/api/v1/data/ingest",
            trace_id,
            {
                "readingId": meter_data.get("readingId"),
                "meters": meter_data.get("meters", []),
                "count": meter_data.get("count", 0),
            },
        )