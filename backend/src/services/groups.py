from sqlalchemy.orm import Session

from fastapi import HTTPException, status

from src.constants import (
    GROUP_EVENT_MEMBER_ADDED,
    GROUP_EVENT_MEMBER_JOINED,
    GROUP_EVENT_MEMBER_LEFT,
    GROUP_EVENT_MEMBER_REMOVED,
    GROUP_LIFECYCLE_ACTIVE,
    GROUP_LIFECYCLE_DISSOLVED,
)
from src.models.group import Group, GroupMembership
from src.models.user import User
from src.services.audit import record


def is_full(group: Group) -> bool:
    return len(group.members) >= group.unit.max_group_size


def ensure_can_join(group: Group, user: User, override_max_size: bool = False) -> None:
    """Raises 409 unless the given user can be placed in the given group.

    override_max_size lets staff place a member past the unit's maximum group
    size.
    """
    if any(g.unit_id == group.unit_id for g in user.groups):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already in a group for this unit")

    if group.lifecycle != GROUP_LIFECYCLE_ACTIVE or not group.members:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Group is no longer active")

    if not override_max_size and is_full(group):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Group is full")


def add_member(db: Session, group: Group, user_id: int, actor_user_id: int, detail: dict | None = None) -> None:
    """Adds a member to a group, without committing.

    Caller needs to commit transaction.
    """
    db.add(GroupMembership(user_id=user_id, group_id=group.id))

    joined_voluntarily = actor_user_id == user_id
    record(
        db,
        group.unit_id,
        GROUP_EVENT_MEMBER_JOINED if joined_voluntarily else GROUP_EVENT_MEMBER_ADDED,
        actor_user_id=actor_user_id,
        subject_user_id=user_id,
        group=group,
        detail=detail,
    )


def remove_member(db: Session, group: Group, user_id: int, actor_user_id: int) -> None:
    """Drops a member from a group, without committing.

    Serves both student self-removal and staff removal: which of the two it was
    is recorded by comparing the actor against the subject.

    A group that loses its last member becomes dissolved: not joinable, and not
    returned by other endpoints that list groups.

    Caller needs to commit.
    """
    was_last_member = len(group.members) == 1

    membership = db.query(GroupMembership).filter_by(user_id=user_id, group_id=group.id).first()
    db.delete(membership)

    left_voluntarily = actor_user_id == user_id
    record(
        db,
        group.unit_id,
        GROUP_EVENT_MEMBER_LEFT if left_voluntarily else GROUP_EVENT_MEMBER_REMOVED,
        actor_user_id=actor_user_id,
        subject_user_id=user_id,
        group=group,
    )

    if was_last_member:
        group.lifecycle = GROUP_LIFECYCLE_DISSOLVED
