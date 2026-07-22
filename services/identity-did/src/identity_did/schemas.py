from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class RequestSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class SubjectCreateRequest(RequestSchema):
    name: str = Field(min_length=1)
    type: str = Field(min_length=1)
    public_key: str = Field(alias="publicKey", min_length=1)


class DeviceCreateRequest(RequestSchema):
    device_name: str = Field(alias="deviceName", min_length=1)
    device_type: str = Field(alias="deviceType", min_length=1)
    owner_did: str = Field(alias="ownerDid", min_length=1)
    public_key: str = Field(alias="publicKey", min_length=1)


class StoredRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SubjectRecord(StoredRecord):
    subjectDid: str
    name: str
    type: str
    publicKey: str
    status: Literal["active", "inactive"] = "active"
    createdAt: str


class DeviceRecord(StoredRecord):
    deviceDid: str
    deviceName: str
    deviceType: str
    ownerDid: str
    publicKey: str
    status: Literal["active", "inactive"] = "active"
    createdAt: str


class AuthorizationRecord(StoredRecord):
    authId: str
    status: Literal["requested", "approved", "rejected", "expired"]
    requesterDid: str
    ownerDid: str
    assetId: str
    purpose: str
    expireAt: str
    decision: Literal["approved", "rejected"] | None = None
    reason: str | None = None
    approverDid: str | None = None
    createdAt: str
    approvedAt: str | None = None


class StoredResult(StoredRecord):
    fingerprint: str
    data: dict[str, Any]
