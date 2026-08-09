# Backlog

Ideas raised during the frontend UI rework (`unit-owned-groups-ui` branch,
`docs/superpowers/specs/2026-08-08-frontend-ui-rework-design.md`) that need
backend design/implementation work and were deliberately deferred rather than
folded into that rework. For whoever picks up backend work next.

## 1. Switch availability grid from 2-hour blocks to 1-hour sections

**Current state:** `backend/src/constants.py` defines a global `TIME_SLOTS`
frozenset: 5 days × 3 periods (`Morning`/`Afternoon`/`Evening`) = 15 slots,
e.g. `mondayMorning`. The frontend's `frontend/src/lib/timeslots.ts` mirrors
this with `DAYS`/`PERIODS` constants.

**What would change:** both constant lists would need more entries (e.g.
hourly labels like `9am`, `10am`, ... instead of `Morning`/`Afternoon`/
`Evening`). Nothing else in the backend hardcodes "3 periods" — slot strings
are stored as an opaque JSON list (`UnitProfile.time_preferences`) and the
group-matching logic (`GET /groups/{unit_id}/{group_id}/recommended-times`)
just intersects sets of strings, so it's agnostic to how many slots exist.

**Risk:** low — this is a small, mechanical change to two files
(`backend/src/constants.py`, `frontend/src/lib/timeslots.ts`), not a
structural change. Existing stored `time_preferences` data using the old
3-period slot names would no longer validate/match against a new hourly
`TIME_SLOTS` set, so it would need a data migration or a decision to
wipe/reset existing availability data.

## 2. Per-unit customizable availability (some units don't run every day/slot)

**Current state:** `TIME_SLOTS` is one global set shared by every unit in
the system. There is no concept of "this unit's schedule" — a unit that only
runs Tuesday/Thursday has no way to express that; students would still see
all 5 days in the grid.

**What this would need:**
- A new field on `Unit` (e.g. `available_slots: list[str]`, stored as JSON
  like `UnitProfile.time_preferences` is) — set at unit creation or
  configurable by the unit owner afterward.
- `UnitProfileUpdate.validate_time_preferences` (currently a stateless
  Pydantic `@field_validator` with no database access) would need to move
  into the router (`update_my_unit_profile` in
  `backend/src/routers/units.py`), since validating "is this slot valid for
  *this* unit" requires a DB lookup the validator doesn't have access to.
- A new endpoint for a unit owner to set/update their unit's available
  slots, and a small UI for it (likely on the Join/Create Unit or a future
  "Manage Unit" screen).
- The frontend's `TimeGrid` component would need to accept which slots are
  actually offered (rather than always rendering the full `DAYS`/`PERIODS`
  grid) and grey out/hide unavailable ones.

**Risk:** moderate — this is a real feature, not a tweak. Worth its own
design pass (brainstorming → spec → plan) rather than being folded into
another feature's implementation.
