from typing import Iterable

from src.constants import TIME_SLOT_ORDER
from src.models.user import User


def common_time_slots(members: Iterable[User], unit_id: int) -> list[str]:
    """The slots every one of the given members is available for in this unit.

    Availability is per-unit, so a member with no profile for this unit — or one
    who has set no preferences — contributes an empty set and empties the whole
    intersection. Returns chronological order, and an empty list when given no
    members to intersect.
    """
    preferences = []
    for member in members:
        profile = next((p for p in member.unit_profiles if p.unit_id == unit_id), None)
        preferences.append(set(profile.time_preferences if profile else []))

    if not preferences:
        return []

    common = set.intersection(*preferences)
    return [slot for slot in TIME_SLOT_ORDER if slot in common]
