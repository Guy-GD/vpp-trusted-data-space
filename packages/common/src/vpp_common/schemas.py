from pydantic import BaseModel, ConfigDict


class CommonSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HealthData(CommonSchema):
    service: str
    status: str


class ErrorDetail(CommonSchema):
    field: str
    reason: str
