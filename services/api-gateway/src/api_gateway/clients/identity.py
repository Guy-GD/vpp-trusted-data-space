from uuid import uuid4

from .base import BaseMockClient


class IdentityClient(BaseMockClient):

    def __init__(self):
        super().__init__(
            "identity-service"
        )

    async def authorize(
        self,
        participants: list[str],
        trace_id: str,
    ) -> dict:
        """
        Verify participant identities.
        """

        return {
            "authorizationId": f"auth_{uuid4().hex[:8]}",
            "participants": participants,
            "authorized": True,
            "status": "AUTHORIZED",
            "traceId": trace_id,
        }