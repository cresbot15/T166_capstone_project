from typing import TYPE_CHECKING

from sqlalchemy.orm import Session
from src.models.unit_event import UnitEvent

if TYPE_CHECKING:
    from src.models.group import Group


def record(
    db: Session,
    unit_id: int,
    event_type: str,
    actor_user_id: int,
    subject_user_id: int | None = None,
    group: "Group | None" = None,
    detail: dict | None = None,
) -> UnitEvent:
    """Adds an audit event to the session without committing it.

    Caller needs to commit.
    """
    event = UnitEvent(
        unit_id=unit_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        subject_user_id=actor_user_id if subject_user_id is None else subject_user_id,
        group_id=group.id if group else None,
        detail=detail,
    )
    db.add(event)
    return event
