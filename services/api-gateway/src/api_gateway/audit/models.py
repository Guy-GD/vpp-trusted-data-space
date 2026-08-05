from datetime import datetime
from pydantic import BaseModel, Field



class AuditEvent(BaseModel):
    """
    Audit event model.

    Used for trusted audit chain.
    """


    traceId: str


    businessId: str


    stage: str


    service: str


    action: str


    status: str = "SUCCESS"


    timestamp: datetime = Field(
        default_factory=datetime.utcnow
    )


    detail: dict = Field(
        default_factory=dict
    )


    # R10 hash chain fields

    previousHash: str | None = None


    eventHash: str | None = None