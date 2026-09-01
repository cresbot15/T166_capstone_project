from datetime import datetime, timezone
from typing import Annotated

from pydantic import PlainSerializer, WithJsonSchema


def _as_utc_iso(value: datetime) -> str:
    """SQLite drops the offset from timestamps, add it back when we need it"""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


UtcDatetime = Annotated[
    datetime,
    PlainSerializer(_as_utc_iso, return_type=str),
    WithJsonSchema({"type": "string", "format": "date-time"}),
]
