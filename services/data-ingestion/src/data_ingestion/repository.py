from __future__ import annotations

import hashlib
import json
import threading
from typing import Callable, Optional, TypeVar

from vpp_common import new_id

from .schemas import AssetData, CreateAssetRequest, DataIngestRequest, IngestData

T = TypeVar("T")


class IngestRepository:
    """In-memory idempotency store + asset registry."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._idempotency: dict[str, tuple[str, IngestData | AssetData]] = {}
        self._assets: dict[str, AssetData] = {}

    # ---- idempotency -----------------------------------------------------------

    def _hash_body(self, body: dict) -> str:
        """Deterministic hash of a plain dict for idempotency comparison."""
        raw = json.dumps(body, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    def idempotency_check(
        self, key: str, body_hash: str
    ) -> Optional[IngestData | AssetData]:
        stored_hash, cached = self._idempotency.get(key, (None, None))  # type: ignore[assignment]
        if stored_hash is None:
            return None
        if stored_hash != body_hash:
            from vpp_common.errors import ErrorCode
            from vpp_common.fastapi_support import ServiceError

            raise ServiceError(
                ErrorCode.IDEMPOTENCY_CONFLICT,
                details=[{"field": "Idempotency-Key", "reason": "same key, different request body"}],
            )
        return cached

    def idempotency_save(self, key: str, body_hash: str, result: IngestData | AssetData) -> None:
        self._idempotency[key] = (body_hash, result)

    def execute_idempotent(self, key: str, body_hash: str, action: Callable[[], T]) -> T:
        """Atomically check → action → save under RLock to prevent races."""
        with self._lock:
            cached = self.idempotency_check(key, body_hash)
            if cached is not None:
                return cached  # type: ignore[return-value]
            result = action()
            self.idempotency_save(key, body_hash, result)
            return result

    # ---- assets ----------------------------------------------------------------

    def save_asset(self, asset: AssetData) -> None:
        self._assets[asset.assetId] = asset

    def get_asset(self, asset_id: str) -> Optional[AssetData]:
        return self._assets.get(asset_id)


# module-level singleton
repo = IngestRepository()
