DEFAULT_MAX_GROUP_SIZE = 5
MIN_MAX_GROUP_SIZE = 2
MAX_MAX_GROUP_SIZE = 20

TIME_SLOTS: frozenset[str] = frozenset({
    "mondayMorning", "mondayAfternoon", "mondayEvening",
    "tuesdayMorning", "tuesdayAfternoon", "tuesdayEvening",
    "wednesdayMorning", "wednesdayAfternoon", "wednesdayEvening",
    "thursdayMorning", "thursdayAfternoon", "thursdayEvening",
    "fridayMorning", "fridayAfternoon", "fridayEvening",
})
