from datetime import datetime, timezone


def utc_now_iso() -> str:
    """Return a timezone-aware ISO 8601 timestamp in UTC."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )
