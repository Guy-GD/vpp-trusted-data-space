import hashlib
import json


def calculate_event_hash(data: dict) -> str:
    """
    Calculate SHA256 hash for audit event.

    The same input data will always produce
    the same hash.
    """

    content = json.dumps(
        data,
        sort_keys=True,
        ensure_ascii=False,
    )

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()