from typing import Any

from vpp_common import ErrorCode, ServiceError, utc_now_iso

from .repository import InMemoryRepository
from .schemas import (
    DeviceCreateRequest,
    DeviceRecord,
    SubjectCreateRequest,
    SubjectRecord,
)


class IdentityService:
    def __init__(self, repository: InMemoryRepository) -> None:
        self.repository = repository

    def register_subject(self, request: SubjectCreateRequest) -> dict[str, Any]:
        subject_did = self.repository.next_subject_did(request.type)
        record = SubjectRecord(
            subjectDid=subject_did,
            name=request.name,
            type=request.type,
            publicKey=request.public_key,
            status="active",
            createdAt=utc_now_iso(),
        )
        self.repository.subjects[subject_did] = record
        return record.model_dump(
            include={"subjectDid", "name", "type", "status", "createdAt"}
        )

    def register_device(self, request: DeviceCreateRequest) -> dict[str, Any]:
        owner = self.repository.subjects.get(request.owner_did)
        if owner is None or owner.status != "active":
            raise ServiceError(ErrorCode.INVALID_DID)

        device_did = self.repository.next_device_did(request.device_type)
        record = DeviceRecord(
            deviceDid=device_did,
            deviceName=request.device_name,
            deviceType=request.device_type,
            ownerDid=request.owner_did,
            publicKey=request.public_key,
            status="active",
            createdAt=utc_now_iso(),
        )
        self.repository.devices[device_did] = record
        return record.model_dump(
            include={"deviceDid", "ownerDid", "status", "createdAt"}
        )
