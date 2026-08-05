from uuid import uuid4

from .base import BaseMockClient


class LedgerClient(BaseMockClient):

    def __init__(self):
        super().__init__(
            "trusted-ledger"
        )

    async def record(
        self,
        asset_id: str,
        trace_id: str,
    ) -> dict:
        """
        Store evidence record.
        """

        return {
            "ledgerId": f"ledger_{uuid4().hex[:8]}",
            "assetId": asset_id,
            "recordStatus": "CONFIRMED",
            "traceId": trace_id,
        }