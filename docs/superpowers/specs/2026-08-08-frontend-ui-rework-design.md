# TeamUp Frontend UI Rework — Design

## Overview

The current frontend (login/register/profile/group pages) is built against an older data
model: one global profile per user, one group per user, no units, no roles. The backend
has since moved to a unit-scoped model (`unit-owned-groups` branch): students join/create
`Unit`s, have a per-unit `UnitProfile` (delivery mode, skills, availability), hold a
per-unit role (`owner`/`administrator`/`student`), and groups belong to a unit and carry
an `is_public` flag.

A set of wireframes (`UI Screenshots/`) sketch a redesigned UI — Home dashboard, Explore
Students & Groups, Create a Group, Register, Profile — using a navy/purple/amber palette.
This spec reworks the frontend to match those wireframes' layouts and flows, restyled to
a more polished/professional finish (same palette), and reconciled against what the
backend actually supports today.

## Goals

- Rebuild the frontend around the unit-scoped backend model (per-unit profile, roles,
  group visibility).
- Match the wireframes' screens and general layout: Home, Explore Students & Groups,
  Create a Group, Register, Profile.
- Restyle to a consistent, professional look using the existing navy `#1E1B3A` / purple
  `#6B46C1` / amber `#F5A623` palette — light lavender backgrounds on every page (no dark
  full-page screens).
- Support students belonging to multiple units via a unit switcher; every unit-scoped
  page (Home, Explore, Group, Profile) operates on one "active unit" at a time.

## Non-goals (explicitly deferred)

- **Custom per-unit fields** (e.g. a unit admin defining extra profile questions like
  "international student?"). No backend support exists; would need a new schema. Not
  part of this rework — but Unit Setup will carry a clearly marked code comment/TODO
  noting where admin-defined questions would render once that feature exists, so it's
  easy to find later.
- **Pre-provisioned/admin-created accounts.** Registration stays self-serve only.
- **Student ID field.** No backend field exists; dropped from Register.
- **A real "Explore Students & Groups" backend endpoint.** No endpoint exists to list a
  unit's students with degree/skills/group-status. This screen ships against mocked
  frontend data, clearly marked as placeholder in code.
- **Discussion Board.** No backend/route exists; cut from the Home dashboard entirely.
- **A real due-date for the countdown timer.** No `due_date` field exists on `Unit`;
  the countdown uses a static placeholder date in frontend code.
- **A "pending approval from the teaching team" group status.** No backend concept of
  staff approval exists. The UI uses the backend's actual statuses (`valid` /
  `provisional`) with accurate copy instead of the wireframe's literal wording.
- Frontend automated tests — out of scope for this pass; verified manually via
  `npm run dev`.

## Architecture

### Routes

| Route | Purpose |
|---|---|
| `/` | Sign in (existing, restyled) |
| `/register` | Create account: first name, last name, email, password |
| `/onboarding/unit` | Join an existing unit by code, or create a new unit (creator becomes `owner`) |
| `/onboarding/setup` | Per-unit setup: delivery mode, skills, availability grid |
| `/home` | Dashboard scoped to the active unit: Create a Group / Explore Students & Groups shortcuts, member-count stat, countdown |
| `/explore` | Explore Students & Groups (mocked student directory + status) |
| `/group` | Create/join a group (if not yet in one for the active unit) or view the active unit's group |
| `/profile` | Schedule, per-unit profile details, "Your Team" summary, edit/logout |

### Active unit

A new `activeUnit` Svelte store (persisted to `localStorage`, alongside the existing
`token`/`user` stores in `src/lib/stores.ts`) holds the id/code/name of the unit currently
being viewed. It is:
- Set when onboarding completes (join or create a unit).
- Changeable via a **unit switcher** dropdown in the navbar, populated from
  `GET /units/me`.
- Read by every unit-scoped API call (`GET/PATCH /units/{id}/me`, `GET/POST
  /groups/{id}...`) instead of threading a unit id through page props.

### Redirect logic

After login: if the student belongs to zero units → `/onboarding/unit`. Otherwise →
`/home` for the active unit (last-selected, or first unit if none was previously chosen).

## Visual design system

Implemented as a custom DaisyUI theme in `app.css` so existing component classes
(`btn`, `card`, `input`, `badge`, etc.) pick it up automatically:

| DaisyUI token | Color | Usage |
|---|---|---|
| `primary` | Navy `#1E1B3A` | Header bars, primary buttons, nav |
| `secondary` | Purple `#6B46C1` | Small accents/icons |
| `accent` / `warning` | Amber `#F5A623` | Status highlights, stat numbers, countdown |
| `success` | Green | "Complete" status |
| `error` | Red | "Incomplete" status |
| `base-100` | White | Cards |
| `base-200` | Light lavender `#EDEAF7` | Page background (every page — no dark full-page screens) |

Typography: system font stack retained. Consistent heading style app-wide
(`font-extrabold tracking-tight` for `h1`/`h2`) replacing the current mix of ad hoc
sizes (`text-xl`, `card-title`, etc.).

### Component inventory

**Shared (thin wrappers over DaisyUI):**
- `PageHeader` — navy bar, logo, title, subtitle slot
- `SectionCard` — the repeated `card bg-base-100` pattern
- `StatusPill` — green/amber/red status indicator

**Bespoke (no DaisyUI equivalent):**
- `TimeGrid` — the availability grid, refactored out of the duplicated inline table
  markup currently in `register`/`profile` into one reusable component (built on
  `src/lib/timeslots.ts`)
- `CountdownTimer` — days/hours/minutes countdown to a (placeholder) date
- `StatDonut` — the "N students registered" donut stat
- `UnitSwitcher` — navbar dropdown listing the student's units

## Page-by-page design

### Register (`/register`)
First/last name, email, password → `POST /auth/register`, then auto-login (existing
behavior retained). Light card on lavender background. No Student ID, no
international-student field, no availability grid (moved to Unit Setup).

### Join/Create Unit (`/onboarding/unit`)
One screen, two paths:
- **Join**: unit code input → `POST /units/join`
- **Create**: optional unit name → `POST /units/create` (caller becomes `owner`)

Either path sets `activeUnit` and routes to Unit Setup. Light background, consistent
with every other screen.

### Unit Setup (`/onboarding/setup`)
Delivery mode (Online/In-person radio), skills (free text), `TimeGrid` availability →
`PATCH /units/{id}/me`. This is the existing register form's availability section,
rehomed here since it's per-unit data. On submit → `/home`.

A code comment/TODO marks the spot below the standard fields where admin-defined
questions would render once a custom-per-unit-field system exists (see Non-goals) —
no component or rendering logic yet, just a clearly flagged insertion point.

### Home (`/home`)
`PageHeader` ("Welcome, {first name}!"), two action buttons (`Create a Group`,
`Explore Students & Groups` — Discussion Board cut), `StatDonut` (unit member count),
`CountdownTimer` (placeholder date, defined as a constant in frontend code).

### Explore Students & Groups (`/explore`)
Search box, degree filter, list of unit students with a `StatusPill`
(green/amber/red). **Mocked data** — seeded with placeholder students, explicitly
commented in code as pending a real `GET /units/{id}/students`-style endpoint. Unit
owner sees an inline role dropdown (`administrator`/`student`) next to each member,
wired to the existing `PATCH /units/{id}/members/{email}` endpoint.

### Group (`/group`)
If not in a group for the active unit: **Create/Join card** — "Create a Group" (name
auto-assigned by backend, Private/Public toggle → `is_public`, `POST /groups/create`)
alongside the existing join-by-code form. Once in a group: member list (starts with
just the creator, grows as others join via the shared code — no backend support for
adding members by name directly), a "copy invite code" action, and status shown as
**valid** (all members share a common time slot) or **provisional** (no shared time
yet, with recommended times surfaced from other members — existing behavior, restyled).

### Profile (`/profile`)
Header with name + Edit Profile/Logout. `SectionCard`s for Schedule (`TimeGrid`,
read-only unless editing) and Profile Details (delivery mode, skills — scoped to the
active unit). "Your Team" card summarizing the active unit's group, or a prompt to
join/create one.

## States

Consistent loading spinner while fetching; empty-state messaging with a call-to-action
where relevant (extending the existing `/group` "no group yet" pattern to `/home`'s
"Your Team" card and `/explore`'s empty search results); inline error text on forms
(existing pattern, retained).

## Testing

Backend pytest suite is untouched (no backend routes are being changed). No frontend
test framework exists today; this rework is verified manually via `npm run dev`
click-through of each flow, not via a new automated frontend test setup.
