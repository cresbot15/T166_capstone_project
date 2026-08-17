# Backlog

Ideas raised during the frontend UI rework (`unit-owned-groups-ui` branch,
`docs/superpowers/specs/2026-08-08-frontend-ui-rework-design.md`) that need
backend design/implementation work and were deliberately deferred rather than
folded into that rework. For whoever picks up backend work next.

## 1. Switch availability grid from named periods to hourly sections

**Current state:** `backend/src/constants.py` defines a global `TIME_SLOTS`
frozenset: 5 days × 3 periods (`Morning`/`Afternoon`/`Evening`) = 15 slots,
e.g. `mondayMorning`. These are opaque labels only — nowhere in the codebase
(backend, frontend, or the original design spec) is `Morning`/`Afternoon`/
`Evening` tied to actual clock hours or a fixed duration like "2-hour
blocks." The frontend's `frontend/src/lib/timeslots.ts` mirrors this with
`DAYS`/`PERIODS` constants.

**What would change:** both constant lists would need more entries (e.g.
hourly labels like `9am`, `10am`, ... instead of `Morning`/`Afternoon`/
`Evening`) — this requires picking a concrete hour range first (e.g. 8am-8pm
hourly = 12 slots/day × 5 days = 60 slots, vs. today's 15; a narrower/wider
range changes the count). Nothing else in the backend hardcodes "3 periods"
— slot strings are stored as an opaque JSON list
(`UnitProfile.time_preferences`) and the group-matching logic
(`GET /groups/{unit_id}/{group_id}/recommended-times`) just intersects sets
of strings, so it's agnostic to how many slots exist.

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

## 3. Unit enrollment total for StatDonut

**Current state:** the Home dashboard's donut stat (`StatDonut` component,
`frontend/src/lib/components/StatDonut.svelte`) shows "N students registered"
as a real percentage (`value / total`), matching the wireframe's intent. But
there is no field anywhere representing a unit's total enrollment/capacity —
`Unit` (`backend/src/models/unit.py`) only has `id`, `code`, `name`. The
frontend currently passes a placeholder constant for `total` (see the `TODO`
comment in `StatDonut.svelte` and in the Home page once built), so the
donut's percentage is not yet meaningful against real enrollment numbers.

**What would be needed:** a field on `Unit` (e.g. `expected_enrollment: int
| None`), settable by the unit owner (likely at creation time, alongside
name/code), and returned on `UnitResponse` so the frontend can compute a
real percentage instead of using the placeholder.

**Risk:** low — a single new column plus exposing it on the existing
response schema. No validation complexity like the time-slot items above.

## 4. Real "who's in this unit" endpoint for Explore

**Current state:** the Explore page's student directory (`/explore`) is
fully mocked (`frontend/src/lib/mockStudents.ts`, ~5 hardcoded rows), per
the original design spec's non-goals ("no endpoint exists to list a unit's
students with degree/skills/group-status"). It's not scoped to the active
unit at all — the same 5 mock rows show regardless of which unit you're
viewing, which reads as broken once you actually expect per-unit
filtering. The desired real behavior: show only users with a real
`UnitMembership` in the active unit (a user can belong to multiple units,
which the data model already supports fine — `UnitMembership` is a
plain many-to-many join with no such restriction).

**What this would need:**
- A new endpoint, e.g. `GET /units/{unit_id}/members`, joining
  `UnitMembership` (for who + role) with `UnitProfile` (for `skills`,
  `delivery_mode`, `is_new_student`) for every member of that unit.
- **`degree` has no backend field anywhere** (not on `User`, not on
  `UnitProfile`) — the mock data invented it. Decide: drop it from the real
  version, or add a real column (small schema change, similar in shape to
  item 3 above).
- **`status` (complete/incomplete/pending in the mock data) has no obvious
  real equivalent** — needs a concrete definition before it can be driven
  by real data, e.g. "unit-setup profile complete" (has delivery
  mode/skills/time preferences filled in) vs. "already in a group for this
  unit" vs. something else. Whichever is picked determines what the new
  endpoint needs to compute/join against (e.g. group membership requires
  also joining `Group`/`GroupMembership` scoped to the unit).
- Frontend: replace `mockStudents` usage in `/explore` with a new
  `api.getUnitMembers(unitId)` call; `StatusPill` stays as-is once `status`
  has a real definition to map onto its three states.

**Risk:** low-to-moderate — the membership+profile join is straightforward
(no new tables needed beyond maybe a `degree` column), but the `status`
definition is a product decision, not just an implementation detail, so
it's worth confirming that before writing the endpoint.
