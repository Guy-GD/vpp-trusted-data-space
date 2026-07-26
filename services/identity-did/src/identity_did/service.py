import base64
import binascii
import hashlib
import hmac
import json
import re
from datetime import datetime, timezone
from typing import Any, Callable, Protocol

import vpp_common
from vpp_common import ErrorCode, ServiceError

from .repository import InMemoryRepository
from .schemas import (
    AuthorizationCreateRequest,
    AuthorizationDecisionRequest,
    AuthorizationRecord,
    DeviceCreateRequest,
    DeviceRecord,
    IdentityVerifyRequest,
    SubjectCreateRequest,
    SubjectRecord,
)


PAYLOAD_HASH_PATTERN = re.compile(r"^sha256:[0-9a-fA-F]{64}$")


class Clock(Protocol):
    def now(self) -> datetime: ...

    def now_iso(self) -> str: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.fromisoformat(
            vpp_common.utc_now_iso().replace("Z", "+00:00")
        )

    def now_iso(self) -> str:
        return vpp_common.utc_now_iso()


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
        if did is None:
            raise ServiceError(ErrorCode.INVALID_REQUEST)
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
        replay_validation: Callable[[], None] | None = None,
    ) -> dict[str, Any]:
        if key is None:
            return action()

        fingerprint = self._fingerprint(operation, payload)
        data = self.repository.execute_idempotent(
            key=key,
            fingerprint=fingerprint,
            action=action,
            replay_validation=replay_validation,
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


class AuthorizationService:
    def __init__(self, repository: InMemoryRepository, clock: Clock) -> None:
        self.repository = repository
        self.clock = clock

    @staticmethod
    def require_matching_caller(caller: str | None, expected: str) -> None:
        if caller is not None and caller.strip() != expected:
            raise ServiceError(ErrorCode.INVALID_DID)

    def create_authorization(
        self,
        request: AuthorizationCreateRequest,
    ) -> dict[str, Any]:
        self._require_active_subject(request.requester_did)
        self._require_active_subject(request.owner_did)

        try:
            now, created_at = self._normalize_timestamp(self.clock.now())
            expire_at, normalized_expiry = self._normalize_timestamp(
                request.expire_at
            )
        except (OverflowError, OSError, TypeError, ValueError):
            raise ServiceError(ErrorCode.INVALID_TIMESTAMP)

        if expire_at <= now:
            raise ServiceError(ErrorCode.INVALID_TIMESTAMP)

        while True:
            record = AuthorizationRecord(
                authId=vpp_common.new_id("auth_"),
                status="requested",
                requesterDid=request.requester_did,
                ownerDid=request.owner_did,
                assetId=request.asset_id,
                purpose=request.purpose,
                expireAt=normalized_expiry,
                decision=None,
                reason=None,
                approverDid=None,
                createdAt=created_at,
                approvedAt=None,
            )
            saved = self.repository.create_authorization(record)
            if saved is not None:
                return saved.model_dump()

    def get_authorization(self, auth_id: str) -> dict[str, Any]:
        now = self._current_time()
        record, outcome = self.repository.update_authorization(
            auth_id,
            lambda current: self._refresh_expiry(current, now),
        )
        if record is None:
            raise ServiceError(ErrorCode.RESOURCE_NOT_FOUND)
        if outcome == "expired":
            raise ServiceError(ErrorCode.AUTHORIZATION_EXPIRED)
        return record.model_dump()

    def require_not_expired(self, auth_id: str) -> None:
        now = self._current_time()
        record, outcome = self.repository.update_authorization(
            auth_id,
            lambda current: self._refresh_expiry(current, now),
        )
        if record is None:
            raise ServiceError(ErrorCode.RESOURCE_NOT_FOUND)
        if outcome == "expired":
            raise ServiceError(ErrorCode.AUTHORIZATION_EXPIRED)

    def decide_authorization(
        self,
        auth_id: str,
        request: AuthorizationDecisionRequest,
    ) -> dict[str, Any]:
        now, approved_at = self._current_time_with_text()

        def decide(
            current: AuthorizationRecord,
        ) -> tuple[AuthorizationRecord, str]:
            refreshed, outcome = self._refresh_expiry(current, now)
            if outcome == "expired":
                return refreshed, outcome
            if refreshed.status != "requested":
                return refreshed, "invalid_state"
            if refreshed.ownerDid != request.approver_did:
                return refreshed, "access_denied"

            refreshed.status = request.decision
            refreshed.decision = request.decision
            refreshed.reason = request.reason
            refreshed.approverDid = request.approver_did
            refreshed.approvedAt = approved_at
            return refreshed, "decided"

        record, outcome = self.repository.update_authorization(auth_id, decide)
        if record is None:
            raise ServiceError(ErrorCode.RESOURCE_NOT_FOUND)
        if outcome == "expired":
            raise ServiceError(ErrorCode.AUTHORIZATION_EXPIRED)
        if outcome == "invalid_state":
            raise ServiceError(ErrorCode.INVALID_RESOURCE_STATE)
        if outcome == "access_denied":
            raise ServiceError(ErrorCode.ACCESS_DENIED)
        return record.model_dump()

    def _require_active_subject(self, subject_did: str) -> SubjectRecord:
        subject = self.repository.get_subject(subject_did)
        if subject is None or subject.status != "active":
            raise ServiceError(ErrorCode.INVALID_DID)
        return subject

    def _current_time(self) -> datetime:
        now, _ = self._current_time_with_text()
        return now

    def _current_time_with_text(self) -> tuple[datetime, str]:
        try:
            return self._normalize_timestamp(self.clock.now())
        except (OverflowError, OSError, TypeError, ValueError):
            raise ServiceError(ErrorCode.INVALID_TIMESTAMP) from None

    @staticmethod
    def _refresh_expiry(
        record: AuthorizationRecord,
        now: datetime,
    ) -> tuple[AuthorizationRecord, str]:
        if record.status == "expired":
            return record, "expired"
        if record.status not in {"requested", "approved"}:
            return record, "active"

        try:
            expire_at = datetime.fromisoformat(
                record.expireAt.replace("Z", "+00:00")
            )
            normalized_expiry, _ = AuthorizationService._normalize_timestamp(
                expire_at
            )
        except (OverflowError, OSError, TypeError, ValueError):
            raise ServiceError(ErrorCode.INVALID_TIMESTAMP) from None

        if normalized_expiry <= now:
            record.status = "expired"
            return record, "expired"
        return record, "active"

    @staticmethod
    def _normalize_timestamp(value: datetime) -> tuple[datetime, str]:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")
        utc_value = value.astimezone(timezone.utc)
        normalized = utc_value.replace(
            microsecond=(utc_value.microsecond // 1000) * 1000
        )
        formatted = normalized.isoformat(timespec="milliseconds").replace(
            "+00:00", "Z"
        )
        return normalized, formatted
