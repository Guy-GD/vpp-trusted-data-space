from uuid import uuid4

from .base import BaseMockClient


class AgentClient(BaseMockClient):

    def __init__(self):
        super().__init__(
            "agent-service"
        )

    async def generate_report(
        self,
        model_version: str,
        trace_id: str,
    ) -> dict:
        """
        Generate final agent report.
        """

        return {
            "agentReportId": (
                f"report_{uuid4().hex[:8]}"
            ),
            "modelVersion": model_version,
            "recommendation": (
                "day-ahead trading optimization"
            ),
            "status": "AGENT_COMPLETED",
            "traceId": trace_id,
        }