from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.group import Group
    from src.models.unit import Unit

MIN_GROUP_SIZE = "min_group_size"
COMMON_TIME_SLOT = "common_time_slot"
MAX_NEW_STUDENTS = "max_new_students"


def count_new_students(group: "Group") -> int:
    count = 0
    for member in group.members:
        profile = next((p for p in member.unit_profiles if p.unit_id == group.unit_id), None)
        if profile and profile.is_new_student:
            count += 1
    return count


def evaluate_group(group: "Group", unit: "Unit") -> list[str]:
    unmet = []

    if len(group.members) < unit.min_group_size:
        unmet.append(MIN_GROUP_SIZE)

    if not group.common_time_slots:
        unmet.append(COMMON_TIME_SLOT)

    if unit.max_new_students is not None and count_new_students(group) > unit.max_new_students:
        unmet.append(MAX_NEW_STUDENTS)

    return unmet
