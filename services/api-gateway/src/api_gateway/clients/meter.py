from uuid import uuid4

from .base import BaseMockClient


class MeterClient(BaseMockClient):

    def __init__(self):
        super().__init__(
            "meter-simulator"
        )


    async def collect_readings(
        self,
        meter_count: int,
        trace_id: str,
    ) -> dict:
        """
        Generate mock meter readings.
        """

        readings = []

        for index in range(meter_count):
            readings.append(
                {
                    "meterId": f"meter_{index+1}",
                    "power": 100 + index * 5,
                    "voltage": 220,
                    "frequency": 50,
                }
            )

        return {
            "readingId": f"reading_{uuid4().hex[:8]}",
            "meters": readings,
            "count": len(readings),
            "traceId": trace_id,
        }