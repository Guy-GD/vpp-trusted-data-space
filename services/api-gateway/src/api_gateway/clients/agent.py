from .base import BaseClient
from ..settings import get_settings


class AgentClient(BaseClient):
    def __init__(self, *, transport=None):
        settings = get_settings()
        super().__init__(
            settings.agent_service_url,
            timeout=settings.http_timeout_seconds,
            transport=transport,
        )

    async def generate_report(self, model_version: str, trace_id: str) -> dict:
        return await self.post(
            "/api/v1/agent/audit-report",
            trace_id,
            {"modelVersion": model_version},
        )