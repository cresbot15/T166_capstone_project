from datetime import datetime, timezone


def utc_now() -> datetime:
    """Current UTC time as a timezone-aware datetime"""
    return datetime.now(timezone.utc)


def current_iso_timestamp() -> str:
    """Current UTC time as an ISO 8601 string"""
    return utc_now().isoformat().replace("+00:00", "Z")
