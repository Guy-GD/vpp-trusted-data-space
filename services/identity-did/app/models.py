from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SubjectCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    name: str = Field(min_length=1)
    type: str = Field(min_length=1)
    public_key: str = Field(alias="publicKey", min_length=1)


class DeviceCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    device_name: str = Field(alias="deviceName", min_length=1)
    device_type: str = Field(alias="deviceType", min_length=1)
    owner_did: str = Field(alias="ownerDid", min_length=1)
    public_key: str = Field(alias="publicKey", min_length=1)


class IdentityVerifyRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    subject_did: str | None = Field(default=None, alias="subjectDid", min_length=1)
    device_did: str | None = Field(default=None, alias="deviceDid", min_length=1)
    signature: str = Field(min_length=1)
    payload_hash: str = Field(alias="payloadHash", min_length=1)

    @model_validator(mode="after")
    def require_exactly_one_did(self) -> "IdentityVerifyRequest":
        if (self.subject_did is None) == (self.device_did is None):
            raise ValueError("provide exactly one of subjectDid or deviceDid")
        return self


class AuthorizationCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    requester_did: str = Field(alias="requesterDid", min_length=1)
    owner_did: str = Field(alias="ownerDid", min_length=1)
    asset_id: str = Field(alias="assetId", min_length=1)
    purpose: str = Field(min_length=1)
    expire_at: datetime = Field(alias="expireAt")


class AuthorizationDecisionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    approver_did: str = Field(alias="approverDid", min_length=1)
    decision: Literal["approved", "rejected"] = "approved"
    reason: str | None = None
