from pydantic import BaseModel, Field
from typing import List, Literal
from datetime import datetime


class ModelUpdate(BaseModel):
    participantDid: str = Field(..., description="Participant DID")
    modelUpdateUri: str = Field(..., description="URI to model update")
    updateHash: str = Field(..., description="SHA256 hash of update")


class SecureAggregateRequest(BaseModel):
    trainingTaskId: str
    roundId: int
    updates: List[ModelUpdate] = Field(..., min_length=2)
    privacyMode: Literal["homomorphic_demo", "secure_masking", "mpc_demo"]


class AggregateResponse(BaseModel):
    aggregateId: str
    trainingTaskId: str
    roundId: int
    aggregateResultUri: str
    aggregateHash: str
    participantCount: int
    privacyMode: str
    createdAt: datetime = Field(default_factory=datetime.utcnow)


class EncryptRequest(BaseModel):
    plaintext: str
    participantDid: str


class MaskRequest(BaseModel):
    updateId: str
    maskingType: Literal["random", "differential_privacy"]