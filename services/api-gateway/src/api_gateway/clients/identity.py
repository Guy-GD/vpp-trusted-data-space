from .base import BaseClient
from ..settings import get_settings


class IdentityClient(BaseClient):
    def __init__(self, *, transport=None):
        settings = get_settings()
        super().__init__(
            settings.identity_service_url,
            timeout=settings.http_timeout_seconds,
            transport=transport,
        )

    async def authorize(self, participants: list[str], trace_id: str) -> dict:
        return await self.post(
            "/api/v1/auth/requests",
            trace_id,
            {"participants": participants},
        )