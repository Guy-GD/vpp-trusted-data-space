from typing import Any

from vpp_common import ErrorCode, ServiceError

from .repository import InMemoryRepository
from .schemas import (
    DeviceCreateRequest,
    SubjectCreateRequest,
)


class IdentityService:
    def __init__(self, repository: InMemoryRepository) -> None:
        self.repository = repository

    def register_subject(self, request: SubjectCreateRequest) -> dict[str, Any]:
        record = self.repository.create_subject(
            name=request.name,
            subject_type=request.type,
            public_key=request.public_key,
        )
        return record.model_dump(
            include={"subjectDid", "name", "type", "status", "createdAt"}
        )

    def register_device(self, request: DeviceCreateRequest) -> dict[str, Any]:
        record = self.repository.create_device(
            device_name=request.device_name,
            device_type=request.device_type,
            owner_did=request.owner_did,
            public_key=request.public_key,
        )
        if record is None:
            raise ServiceError(ErrorCode.INVALID_DID)
        return record.model_dump(
            include={"deviceDid", "ownerDid", "status", "createdAt"}
        )
