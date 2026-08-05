from uuid import uuid4

from .base import BaseMockClient


class IngestionClient(BaseMockClient):

    def __init__(self):
        super().__init__(
            "data-ingestion"
        )

    async def register_asset(
        self,
        meter_data: dict,
        trace_id: str,
    ) -> dict:
        """
        Register collected data asset.
        """

        return {
            "assetId": f"asset_{uuid4().hex[:8]}",
            "source": "meter-simulator",
            "status": "REGISTERED",
            "meterCount": meter_data.get(
                "count",
                0,
            ),
            "traceId": trace_id,
        }