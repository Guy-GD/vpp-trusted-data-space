from vpp_common import ErrorCode, ServiceError

from .repository import repository


class IdempotencyService:
    def check(self, key: str | None, fingerprint: str):
        if not key:
            return None
        entry = repository.get(key)
        if entry is None:
            return None
        if entry["fingerprint"] != fingerprint:
            raise ServiceError(ErrorCode.IDEMPOTENCY_CONFLICT)
        return entry["result"]

    def save(self, key: str | None, fingerprint: str, result: dict):
        if not key:
            return
        repository.save(key, {"fingerprint": fingerprint, "result": result})


idempotency_service = IdempotencyService()