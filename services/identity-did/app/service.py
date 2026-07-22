import base64
import copy
import hashlib
import hmac
import json
import re
from datetime import datetime
from typing import Any, Callable
from zoneinfo import ZoneInfo

from app.errors import ApiError, success_envelope
from app.store import InMemoryStore, store


CHINA_TZ = ZoneInfo("Asia/Shanghai")
SHA256_PATTERN = re.compile(r"^sha256:[0-9a-fA-F]{64}$")


def now_iso() -> str:
    return datetime.now(CHINA_TZ).isoformat(timespec="seconds")


class IdentityService:
    def __init__(self, repository: InMemoryStore) -> None:
        self.repository = repository

    def register_subject(self, name: str, subject_type: str, public_key: str) -> dict[str, Any]:
        did = self.repository.next_subject_did(subject_type)
        record = {
            "subjectDid": did,
            "name": name,
            "type": subject_type,
            "publicKey": public_key,
            "status": "active",
            "createdAt": now_iso(),
        }
        self.repository.subjects[did] = record
        return self._subject_response(record)

    def register_device(
        self,
        device_name: str,
        device_type: str,
        owner_did: str,
        public_key: str,
    ) -> dict[str, Any]:
        owner = self.repository.subjects.get(owner_did)
        if owner is None or owner["status"] != "active":
            raise ApiError(401, 40102, "invalid did")

        did = self.repository.next_device_did(device_type)
        record = {
            "deviceDid": did,
            "deviceName": device_name,
            "deviceType": device_type,
            "ownerDid": owner_did,
            "publicKey": public_key,
            "status": "active",
            "createdAt": now_iso(),
        }
        self.repository.devices[did] = record
        return self._device_response(record)

    def get_identity(self, did: str) -> dict[str, Any] | None:
        return self.repository.subjects.get(did) or self.repository.devices.get(did)

    @staticmethod
    def make_mock_signature(public_key: str, payload_hash: str) -> str:
        digest = hashlib.sha256(f"{public_key}:{payload_hash}".encode("utf-8")).digest()
        return base64.b64encode(digest).decode("ascii")

    def verify_identity(
        self,
        did: str,
        signature: str,
        payload_hash: str,
    ) -> dict[str, Any]:
        identity = self.get_identity(did)
        if identity is None or identity["status"] != "active":
            raise ApiError(401, 40102, "invalid did")
        if SHA256_PATTERN.fullmatch(payload_hash) is None:
            raise ApiError(401, 40104, "invalid hash")

        expected = self.make_mock_signature(identity["publicKey"], payload_hash)
        if not hmac.compare_digest(signature, expected):
            raise ApiError(401, 40103, "invalid signature")

        subject_type = identity.get("type") or identity["deviceType"]
        return {
            "valid": True,
            "did": did,
            "subjectType": subject_type,
        }

    @staticmethod
    def _subject_response(record: dict[str, Any]) -> dict[str, Any]:
        return {
            key: record[key]
            for key in ("subjectDid", "name", "type", "status", "createdAt")
        }

    @staticmethod
    def _device_response(record: dict[str, Any]) -> dict[str, Any]:
        return {
            key: record[key]
            for key in ("deviceDid", "ownerDid", "status", "createdAt")
        }


identity_service = IdentityService(store)


class AuthorizationService:
    def __init__(
        self,
        repository: InMemoryStore,
        identities: IdentityService,
    ) -> None:
        self.repository = repository
        self.identities = identities

    def create(
        self,
        requester_did: str,
        owner_did: str,
        asset_id: str,
        purpose: str,
        expire_at: datetime,
    ) -> dict[str, Any]:
        self._require_active_subject(requester_did)
        self._require_active_subject(owner_did)
        if expire_at.tzinfo is None or expire_at <= datetime.now(CHINA_TZ):
            raise ApiError(400, 40003, "invalid timestamp")

        auth_id = self.repository.next_authorization_id()
        record = {
            "authId": auth_id,
            "status": "pending",
            "requesterDid": requester_did,
            "ownerDid": owner_did,
            "assetId": asset_id,
            "purpose": purpose,
            "expireAt": expire_at.isoformat(timespec="seconds"),
            "createdAt": now_iso(),
        }
        self.repository.authorizations[auth_id] = record
        return record.copy()

    def get(self, auth_id: str) -> dict[str, Any]:
        record = self.repository.authorizations.get(auth_id)
        if record is None:
            raise ApiError(404, 40401, "resource not found")
        return record.copy()

    def decide(
        self,
        auth_id: str,
        approver_did: str,
        decision: str,
        reason: str | None,
    ) -> dict[str, Any]:
        record = self.repository.authorizations.get(auth_id)
        if record is None:
            raise ApiError(404, 40401, "resource not found")
        if record["status"] != "pending":
            raise ApiError(409, 40902, "invalid resource state")
        if record["ownerDid"] != approver_did:
            raise ApiError(403, 40301, "access denied")

        record["status"] = decision
        record["approverDid"] = approver_did
        record["decidedAt"] = now_iso()
        if reason is not None:
            record["reason"] = reason
        return record.copy()

    def _require_active_subject(self, did: str) -> None:
        identity = self.repository.subjects.get(did)
        if identity is None or identity["status"] != "active":
            raise ApiError(401, 40102, "invalid did")


authorization_service = AuthorizationService(store, identity_service)


class IdempotencyService:
    def __init__(self, repository: InMemoryStore) -> None:
        self.repository = repository

    def execute(
        self,
        key: str | None,
        operation: str,
        payload: dict[str, Any],
        trace_id: str,
        action: Callable[[], dict[str, Any]],
    ) -> dict[str, Any]:
        if key is None:
            return success_envelope(action(), trace_id)

        fingerprint = self._fingerprint(operation, payload)
        existing = self.repository.idempotency_records.get(key)
        if existing is not None:
            if existing["fingerprint"] != fingerprint:
                raise ApiError(409, 40901, "idempotency conflict")
            return copy.deepcopy(existing["response"])

        response = success_envelope(action(), trace_id)
        self.repository.idempotency_records[key] = {
            "fingerprint": fingerprint,
            "response": copy.deepcopy(response),
        }
        return response

    @staticmethod
    def _fingerprint(operation: str, payload: dict[str, Any]) -> str:
        canonical = json.dumps(
            {"operation": operation, "payload": payload},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def require_matching_caller(caller_did: str | None, expected_did: str) -> None:
    if caller_did is not None and caller_did != expected_did:
        raise ApiError(401, 40102, "invalid did")


idempotency_service = IdempotencyService(store)
