# Account-level roles
USER_ROLE_STUDENT = "student"
USER_ROLE_COORDINATOR = "unit_coordinator"
USER_ROLES: tuple[str, ...] = (USER_ROLE_STUDENT, USER_ROLE_COORDINATOR)

UNIT_ROLE_OWNER = "owner"
UNIT_ROLE_ADMINISTRATOR = "administrator"
UNIT_ROLE_STUDENT = "student"
UNIT_ROLES: tuple[str, ...] = (UNIT_ROLE_OWNER, UNIT_ROLE_ADMINISTRATOR, UNIT_ROLE_STUDENT)
UNIT_STAFF_ROLES: tuple[str, ...] = (UNIT_ROLE_OWNER, UNIT_ROLE_ADMINISTRATOR)

# Audit log events
UNIT_EVENT_MEMBER_JOINED = "unit.member_joined"
UNIT_EVENT_MEMBER_LEFT = "unit.member_left"
UNIT_EVENT_ROLE_CHANGED = "unit.role_changed"
GROUP_EVENT_CREATED = "group.created"
GROUP_EVENT_DELETED = "group.deleted"
GROUP_EVENT_MEMBER_JOINED = "group.member_joined"
GROUP_EVENT_MEMBER_LEFT = "group.member_left"
GROUP_EVENT_MEMBER_REMOVED = "group.member_removed"
GROUP_EVENT_STATUS_CHANGED = "group.status_changed"
EVENT_TYPES: tuple[str, ...] = (
    UNIT_EVENT_MEMBER_JOINED,
    UNIT_EVENT_MEMBER_LEFT,
    UNIT_EVENT_ROLE_CHANGED,
    GROUP_EVENT_CREATED,
    GROUP_EVENT_DELETED,
    GROUP_EVENT_MEMBER_JOINED,
    GROUP_EVENT_MEMBER_LEFT,
    GROUP_EVENT_MEMBER_REMOVED,
    GROUP_EVENT_STATUS_CHANGED,
)

DEFAULT_MIN_GROUP_SIZE = 2
MIN_MIN_GROUP_SIZE = 1

DEFAULT_MAX_GROUP_SIZE = 5
MIN_MAX_GROUP_SIZE = 2
MAX_MAX_GROUP_SIZE = 20

DAYS: tuple[str, ...] = (
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
)

# Every hour of every day, named for the hour it starts: "monday00" .. "sunday23".
# Ordered chronologically; TIME_SLOTS is the same set for membership checks.
TIME_SLOT_ORDER: tuple[str, ...] = tuple(
    f"{day}{hour:02d}" for day in DAYS for hour in range(24)
)
TIME_SLOTS: frozenset[str] = frozenset(TIME_SLOT_ORDER)
