from .base import BaseClient
from ..settings import get_settings


class FLClient(BaseClient):
    def __init__(self, *, transport=None):
        settings = get_settings()
        super().__init__(
            settings.fl_service_url,
            timeout=settings.http_timeout_seconds,
            transport=transport,
        )

    async def train(self, asset_id: str, rounds: int, trace_id: str) -> dict:
        return await self.post(
            "/api/v1/fl/tasks",
            trace_id,
            {"assetId": asset_id, "rounds": rounds},
        )