from typing import Dict, Any, Optional


class PrivacyRepository:
    """In-memory repository for mock implementation"""
    
    def __init__(self):
        self._aggregates: Dict[str, Dict[str, Any]] = {}
        self._encryption_records: Dict[str, Dict[str, Any]] = {}
        self._mask_records: Dict[str, Dict[str, Any]] = {}

    def save_aggregate(self, aggregate_id: str, data: Dict[str, Any]):
        self._aggregates[aggregate_id] = data

    def get_aggregate(self, aggregate_id: str) -> Optional[Dict[str, Any]]:
        return self._aggregates.get(aggregate_id)

    def save_encryption_record(self, encryption_id: str, data: Dict[str, Any]):
        self._encryption_records[encryption_id] = data

    def save_mask_record(self, mask_id: str, data: Dict[str, Any]):
        self._mask_records[mask_id] = data