from itertools import count
from typing import Any


class InMemoryStore:
    def __init__(self) -> None:
        self.subjects: dict[str, dict[str, Any]] = {}
        self.devices: dict[str, dict[str, Any]] = {}
        self.authorizations: dict[str, dict[str, Any]] = {}
        self.idempotency_records: dict[str, dict[str, Any]] = {}
        self._subject_ids = count(1)
        self._device_ids = count(1)
        self._authorization_ids = count(1)

    @staticmethod
    def _slug(value: str) -> str:
        return value.strip().lower().replace("_", "-").replace(" ", "-")

    def next_subject_did(self, subject_type: str) -> str:
        return f"did:vpp:{self._slug(subject_type)}:{next(self._subject_ids):03d}"

    def next_device_did(self, device_type: str) -> str:
        return f"did:vpp:{self._slug(device_type)}:{next(self._device_ids):03d}"

    def next_authorization_id(self) -> str:
        return f"auth_{next(self._authorization_ids):03d}"


store = InMemoryStore()
