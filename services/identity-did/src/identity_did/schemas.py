from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)


NonEmptyString = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]
SlugSource = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        pattern=r"^[A-Za-z0-9]+(?:[ _-]+[A-Za-z0-9]+)*$",
    ),
]


class RequestSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=False, extra="forbid")


class SubjectCreateRequest(RequestSchema):
    name: NonEmptyString
    type: SlugSource
    public_key: NonEmptyString = Field(alias="publicKey")


class DeviceCreateRequest(RequestSchema):
    device_name: NonEmptyString = Field(alias="deviceName")
    device_type: SlugSource = Field(alias="deviceType")
    owner_did: NonEmptyString = Field(alias="ownerDid")
    public_key: NonEmptyString = Field(alias="publicKey")


class IdentityVerifyRequest(RequestSchema):
    subject_did: NonEmptyString | None = Field(default=None, alias="subjectDid")
    device_did: NonEmptyString | None = Field(default=None, alias="deviceDid")
    signature: NonEmptyString
    payload_hash: NonEmptyString = Field(alias="payloadHash")

    @model_validator(mode="after")
    def require_exactly_one_did(self) -> "IdentityVerifyRequest":
        if (self.subject_did is None) == (self.device_did is None):
            raise ValueError("exactly one of subjectDid or deviceDid is required")
        return self


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
