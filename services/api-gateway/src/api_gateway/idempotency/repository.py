from typing import Dict


class IdempotencyRepository:
    """
    简单内存幂等存储
    """

    def __init__(self):
        self.storage: Dict[str, dict] = {}

    def get(
        self,
        key: str,
    ):
        return self.storage.get(key)


    def save(
        self,
        key: str,
        result: dict,
    ):
        self.storage[key] = result


repository = IdempotencyRepository()