from .base import BaseClient
from ..settings import get_settings


class LedgerClient(BaseClient):
    def __init__(self, *, transport=None):
        settings = get_settings()
        super().__init__(
            settings.ledger_service_url,
            timeout=settings.http_timeout_seconds,
            transport=transport,
        )

    async def record(self, asset_id: str, trace_id: str) -> dict:
        return await self.post(
            "/api/v1/ledger/events",
            trace_id,
            {"assetId": asset_id, "eventType": "data_asset_registered"},
        )