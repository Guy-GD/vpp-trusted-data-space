from .base import BaseClient
from ..settings import get_settings


class PrivacyClient(BaseClient):
    def __init__(self, *, transport=None):
        settings = get_settings()
        super().__init__(
            settings.privacy_service_url,
            timeout=settings.http_timeout_seconds,
            transport=transport,
        )

    async def execute(self, model_version: str, trace_id: str) -> dict:
        return await self.post(
            "/api/v1/privacy/secure-aggregate",
            trace_id,
            {"modelVersion": model_version},
        )