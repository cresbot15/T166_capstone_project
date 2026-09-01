# Account-level roles
USER_ROLE_STUDENT = "student"
USER_ROLE_COORDINATOR = "unit_coordinator"
USER_ROLES: tuple[str, ...] = (USER_ROLE_STUDENT, USER_ROLE_COORDINATOR)

UNIT_ROLE_OWNER = "owner"
UNIT_ROLE_ADMINISTRATOR = "administrator"
UNIT_ROLE_STUDENT = "student"
UNIT_ROLES: tuple[str, ...] = (UNIT_ROLE_OWNER, UNIT_ROLE_ADMINISTRATOR, UNIT_ROLE_STUDENT)
UNIT_STAFF_ROLES: tuple[str, ...] = (UNIT_ROLE_OWNER, UNIT_ROLE_ADMINISTRATOR)

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
