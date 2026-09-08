from datetime import datetime

from fastapi import HTTPException, status

from src.constants import FORMATION_CLOSED, FORMATION_NOT_OPEN, FORMATION_OPEN
from src.models.unit import Unit
from src.services.timestamps import utc_now


def validate_formation_window(
    start: datetime | None,
    end: datetime | None,
    now: datetime | None = None,
) -> None:
    """Raises ValueError unless the given pair of dates is a usable window."""
    for label, value in (("formation_start_date", start), ("formation_end_date", end)):
        if value is not None and value.tzinfo is None:
            raise ValueError(f"{label} must include a UTC offset")

    if start and end and start >= end:
        raise ValueError("formation_start_date must be before formation_end_date")

    if end and end < (now or utc_now()):
        raise ValueError("formation_end_date cannot be in the past")


def formation_state(unit: Unit, now: datetime | None = None) -> str:
    """Whether the unit's group formation window has opened, and whether it has closed.

    Either date being None leaves that end of the window unbounded. `now` is a
    parameter so callers, and tests in particular, can ask about another moment.
    """
    now = now or utc_now()

    if unit.formation_start_date and now < unit.formation_start_date:
        return FORMATION_NOT_OPEN

    if unit.formation_end_date and now > unit.formation_end_date:
        return FORMATION_CLOSED

    return FORMATION_OPEN


def formation_is_open(unit: Unit, now: datetime | None = None) -> bool:
    return formation_state(unit, now) == FORMATION_OPEN


def require_formation_open(unit: Unit, now: datetime | None = None) -> None:
    """Raises 409 unless groups can currently be formed in this unit."""
    state = formation_state(unit, now)

    if state == FORMATION_NOT_OPEN:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Group formation opens at {unit.formation_start_date.isoformat()}",
        )

    if state == FORMATION_CLOSED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Group formation closed at {unit.formation_end_date.isoformat()}",
        )
