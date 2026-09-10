from sqlalchemy.orm import Session

from src.constants import (
    GROUP_EVENT_MEMBER_LEFT,
    GROUP_EVENT_MEMBER_REMOVED,
    GROUP_LIFECYCLE_DISSOLVED,
)
from src.models.group import Group, GroupMembership
from src.services.audit import record


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
