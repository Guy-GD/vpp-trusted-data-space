from typing import Dict


class IdempotencyRepository:
    """
    In-memory idempotency storage.

    entry = {"fingerprint": str, "result": dict}
    """

    def __init__(self):
        self.storage: Dict[str, dict] = {}

    def get(self, key: str):
        return self.storage.get(key)

    def save(self, key: str, entry: dict):
        self.storage[key] = entry


repository = IdempotencyRepository()