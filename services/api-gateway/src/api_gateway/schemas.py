from typing import Any

from pydantic import BaseModel, Field


class DemoRequest(BaseModel):
    """
    Demo workflow input.
    """

    scenario: str = Field(
        default="vpp_day_ahead_trading"
    )

    participants: list[str]

    meterCount: int = 0

    trainingRounds: int = 1


class DemoResult(BaseModel):
    """
    Workflow output.
    """

    businessId: str

    assetId: str

    globalModelVersion: str

    agentReportId: str

    status: str

    metrics: dict[str, Any] = Field(
        default_factory=dict
    )


class WorkflowState(BaseModel):
    """
    Stored workflow state.
    """

    businessId: str

    request_hash: str

    status: str

    currentStage: str

    traceId: str

    lastEventType: str | None = None

    result: DemoResult | None = None

    error: dict[str, Any] | None = None


class HealthData(BaseModel):
    service: str

    status: str
