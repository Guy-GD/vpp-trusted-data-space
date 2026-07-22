import base64
import binascii
import hashlib
import hmac
import json
import re
from typing import Any, Callable

from vpp_common import ErrorCode, ServiceError

from .repository import InMemoryRepository
from .schemas import (
    DeviceCreateRequest,
    DeviceRecord,
    IdentityVerifyRequest,
    SubjectCreateRequest,
    SubjectRecord,
)


PAYLOAD_HASH_PATTERN = re.compile(r"^sha256:[0-9a-fA-F]{64}$")


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

    def get_identity(self, did: str) -> SubjectRecord | DeviceRecord | None:
        return self.repository.subjects.get(did) or self.repository.devices.get(did)

    @staticmethod
    def make_mock_signature(public_key: str, payload_hash: str) -> str:
        digest = hashlib.sha256(
            f"{public_key}:{payload_hash}".encode("utf-8")
        ).digest()
        return base64.b64encode(digest).decode("ascii")

    def verify_identity(self, request: IdentityVerifyRequest) -> dict[str, Any]:
        did = request.subject_did or request.device_did
        assert did is not None
        identity = self.get_identity(did)
        if identity is None or identity.status != "active":
            raise ServiceError(ErrorCode.INVALID_DID)
        if PAYLOAD_HASH_PATTERN.fullmatch(request.payload_hash) is None:
            raise ServiceError(ErrorCode.INVALID_HASH)

        try:
            signature = base64.b64decode(request.signature, validate=True)
        except (binascii.Error, ValueError):
            raise ServiceError(ErrorCode.INVALID_SIGNATURE) from None

        expected = hashlib.sha256(
            f"{identity.publicKey}:{request.payload_hash}".encode("utf-8")
        ).digest()
        if not hmac.compare_digest(signature, expected):
            raise ServiceError(ErrorCode.INVALID_SIGNATURE)

        subject_type = (
            identity.type
            if isinstance(identity, SubjectRecord)
            else identity.deviceType
        )
        return {
            "valid": True,
            "did": did,
            "subjectType": subject_type,
        }


class IdempotencyService:
    def __init__(self, repository: InMemoryRepository) -> None:
        self.repository = repository

    def execute(
        self,
        key: str | None,
        operation: str,
        payload: dict[str, Any],
        action: Callable[[], dict[str, Any]],
    ) -> dict[str, Any]:
        if key is None:
            return action()

        fingerprint = self._fingerprint(operation, payload)
        data = self.repository.execute_idempotent(
            key=key,
            fingerprint=fingerprint,
            action=action,
        )
        if data is None:
            raise ServiceError(ErrorCode.IDEMPOTENCY_CONFLICT)
        return data

    @staticmethod
    def _fingerprint(operation: str, payload: dict[str, Any]) -> str:
        canonical = json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return hashlib.sha256(f"{operation}:{canonical}".encode("utf-8")).hexdigest()
