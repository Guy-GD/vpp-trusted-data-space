from uuid import uuid4

from .base import BaseMockClient


class PrivacyClient(BaseMockClient):

    def __init__(self):
        super().__init__(
            "privacy-compute"
        )

    async def execute(
        self,
        model_version: str,
        trace_id: str,
    ) -> dict:
        """
        Simulate privacy computation.
        """

        return {
            "taskId": f"privacy_{uuid4().hex[:8]}",
            "modelVersion": model_version,
            "algorithm": "secure-aggregation",
            "status": "COMPLETED",
            "traceId": trace_id,
        }