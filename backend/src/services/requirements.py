from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.group import Group
    from src.models.unit import Unit

MIN_GROUP_SIZE = "min_group_size"
COMMON_TIME_SLOT = "common_time_slot"


def evaluate_group(group: "Group", unit: "Unit") -> list[str]:
    unmet = []

    if len(group.members) < unit.min_group_size:
        unmet.append(MIN_GROUP_SIZE)

    if not group.common_time_slots:
        unmet.append(COMMON_TIME_SLOT)

    return unmet
