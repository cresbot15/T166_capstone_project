# TeamUp Frontend UI Rework — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Execution style override:** the user wants every function/component walked through individually — what it does and why — with approval **between** pieces, not whole tasks dropped at once. Within each task below, after writing a function or component, stop and explain it in 2-4 sentences before moving to the next step, even though the task groups multiple steps together. Favor small, explainable increments over batching. This is a deliberate, standing preference (see memory `feedback_stepwise_frontend_review`) — do not "optimize" it away for speed.

**Goal:** Rebuild the TeamUp frontend from scratch against the unit-scoped backend model (units, per-unit profiles, roles, group visibility), matching the UI wireframes in `UI Screenshots/`, restyled with a consistent light navy/purple/amber theme.

**Architecture:** SvelteKit pages consume a small typed `api.ts` client; a persisted `activeUnit` store (alongside the existing `token`/`user` stores) scopes every unit-dependent call; a handful of shared presentational components (DaisyUI-backed) and bespoke components (no DaisyUI equivalent) are built once and reused across pages.

**Tech Stack:** SvelteKit (Svelte 5, runes mode), TypeScript, Tailwind CSS v4, DaisyUI v5. No new npm dependencies.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-08-08-frontend-ui-rework-design.md` — every task below implements a section of it.
- Every page background is light (`base-200`) — **no dark full-page screens anywhere**, per explicit user direction.
- Exact theme colors (hex, not oklch, so the brand colors are exact): primary `#1E1B3A`, secondary `#6B46C1`, accent/warning `#F5A623`, base-200 `#EDEAF7`, base-100 `#ffffff`.
- All new/rewritten components use Svelte 5 runes (`$state`, `$props`, `$derived`) — the project forces runes mode (`svelte.config.js`).
- Backend base URL stays `http://localhost:8000` (existing pattern in `api.ts`, unchanged).
- No new frontend test framework is introduced (spec Non-goals). Every task instead runs `npm run check` (existing `svelte-check` script) for type/compile errors, plus a manual visual check via `npm run dev` for UI tasks.
- Backend is not modified by this plan — every task calls an endpoint that already exists (verified against `backend/src/routers/*.py` during design).
- Old page implementations are being fully replaced, not patched — write new file contents wholesale rather than diffing against the old logic.

## Current Progress (resume here)

_Last updated: 2026-08-17._

**Done, committed:** Tasks 1-18 (theme, stores, `api.ts` incl. the `getGroups` addition, all 7 components, navbar, Sign In, Register, Join/Create Unit, Unit Setup, Explore), plus **Task 16 and Task 17** (mock data + Home dashboard), which were pulled forward out of plan order at the user's request to get a demoable Home screen quickly. All checked off below. The full sign-up flow (Register → Join/Create Unit → Unit Setup → Home) is now wired end-to-end. Task 18 was extended beyond its original script to add a real (non-mocked) group-browsing/join section — see the scope note under Task 18.

**Not started, resume here: Task 19** (rewrite `/group`). Then 20 (Profile rewrite — these still have the pre-existing `npm run check` errors described throughout the plan), 21 (final verification).

**Known, expected `npm run check` state as of Task 18:** 19 errors, all in `group`/`profile` (unrewritten routes) — the `+layout.svelte` `/explore` route-typing error is now gone since Task 18 created that route folder. Confirmed by running `npm run check` after Task 18's commit.

**Note for Task 19/20:** while investigating Task 18, confirmed the backend has no unit-members/roster-listing endpoint at all (only per-user `GET /units/{id}/me`), which is why Explore's student list must stay mocked. But `GET /groups/{unit_id}` is real and now has an `api.getGroups` client method — worth checking whether Task 19's Group-page rewrite or Task 20's Profile rewrite can make use of it too, since neither was written with it in mind.

**Demo environment set up for this session** (not part of the plan's own tasks, but needed to show working screens):
- Backend: `cd backend && JWT_SECRET="local-dev-demo-secret" .venv/bin/fastapi dev src/main.py` (venv already created from a prior session; `uv` isn't installed on this machine).
- Frontend: `cd frontend && npm run dev`.
- Both dev servers were started again this session (backend pid 11741, frontend pid 11745 as of 2026-08-17) to verify Task 13 — check if still running before restarting.
- A demo account + unit were seeded directly via API calls (not through the UI, since onboarding pages don't exist yet): email `demo@teamup-demo.example.com`, password `demo1234`, unit "IFB398 Capstone". This data lives in the local `backend/app.db` SQLite file (gitignored) — if that file is deleted/recreated, the demo account needs reseeding (same `register` → `login` → `units/create` calls, in that order). A second test account `test-register-check@example.com` / `testpass123` was also created this session while verifying Task 13.

---

### Task 1: DaisyUI custom theme

**Files:**
- Modify: `frontend/src/app.css`

**Interfaces:**
- Produces: DaisyUI theme named `teamup` (default), exposing `--color-primary`, `--color-secondary`, `--color-accent`, `--color-warning`, `--color-success`, `--color-error`, `--color-base-100`, `--color-base-200`, `--color-base-300`, `--color-base-content` — every later task's DaisyUI classes (`btn-primary`, `badge-success`, etc.) and every custom component reading `var(--color-accent)` depend on these existing.

- [x] **Step 1: Write the theme**

Replace the full contents of `frontend/src/app.css` with:

```css
@import 'tailwindcss';
@plugin 'daisyui' {
	themes: teamup --default;
}
@plugin 'daisyui/theme' {
	name: 'teamup';
	default: true;
	color-scheme: light;
	--color-base-100: #ffffff;
	--color-base-200: #EDEAF7;
	--color-base-300: #DAD4EF;
	--color-base-content: #231F3D;
	--color-primary: #1E1B3A;
	--color-primary-content: #ffffff;
	--color-secondary: #6B46C1;
	--color-secondary-content: #ffffff;
	--color-accent: #F5A623;
	--color-accent-content: #231F3D;
	--color-neutral: #1E1B3A;
	--color-neutral-content: #ffffff;
	--color-info: #3B82F6;
	--color-info-content: #ffffff;
	--color-success: #22C55E;
	--color-success-content: #06210F;
	--color-warning: #F5A623;
	--color-warning-content: #231F3D;
	--color-error: #EF4444;
	--color-error-content: #ffffff;
	--radius-selector: 1rem;
	--radius-field: 0.75rem;
	--radius-box: 1rem;
}

body {
	background-color: var(--color-base-200);
}

h1,
h2 {
	font-weight: 800;
	letter-spacing: -0.02em;
}
```

- [x] **Step 2: Type/compile check**

Run: `cd frontend && npm run check`
Expected: no errors (CSS isn't type-checked, but this confirms nothing else broke).

- [x] **Step 3: Visual check**

Run: `cd frontend && npm run dev`, open `http://localhost:5173`. Expected: the sign-in page's background is light lavender and its button is dark navy (DaisyUI's default component classes already pick up the new theme even though no page has been rewritten yet). This exact CSS block was verified against the installed DaisyUI 5.5.20 via `npx vite build` — the compiled output contains `--color-primary:#1e1b3a` and the `teamup` theme name with no warnings, so this step should just confirm the visual result matches.

- [x] **Step 4: Commit**

```bash
git add frontend/src/app.css
git commit -m "style: add teamup DaisyUI theme (navy/purple/amber, light backgrounds)"
```

---

### Task 2: `activeUnit` store

**Files:**
- Modify: `frontend/src/lib/stores.ts`

**Interfaces:**
- Consumes: `UnitResponse` type from `$lib/api` (already exists: `{ id: number; code: string; name: string | null }`).
- Produces: `activeUnit` store with `subscribe`, `set(val: UnitResponse | null)`, `clear()` — same shape as the existing `token` store. Every later page/component reads `$activeUnit` and calls `activeUnit.set(...)` / `activeUnit.clear()`.

- [x] **Step 1: Add the store**

Replace the full contents of `frontend/src/lib/stores.ts` with:

```ts
import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import type { UserResponse, UnitResponse } from '$lib/api';

function createTokenStore() {
	const initial = browser ? localStorage.getItem('token') : null;
	const { subscribe, set } = writable<string | null>(initial);
	return {
		subscribe,
		set(val: string | null) {
			if (browser) {
				if (val) localStorage.setItem('token', val);
				else localStorage.removeItem('token');
			}
			set(val);
		},
		clear() {
			this.set(null);
		}
	};
}

function createActiveUnitStore() {
	const raw = browser ? localStorage.getItem('activeUnit') : null;
	const initial: UnitResponse | null = raw ? JSON.parse(raw) : null;
	const { subscribe, set } = writable<UnitResponse | null>(initial);
	return {
		subscribe,
		set(val: UnitResponse | null) {
			if (browser) {
				if (val) localStorage.setItem('activeUnit', JSON.stringify(val));
				else localStorage.removeItem('activeUnit');
			}
			set(val);
		},
		clear() {
			this.set(null);
		}
	};
}

export const token = createTokenStore();
export const user = writable<UserResponse | null>(null);
export const activeUnit = createActiveUnitStore();
```

- [x] **Step 2: Type/compile check**

Run: `cd frontend && npm run check`
Expected: FAILS — `$lib/api` doesn't export `UnitResponse` yet (Task 3 adds it). This is expected; confirms the store correctly depends on the upcoming API types.

- [x] **Step 3: Commit**

```bash
git add frontend/src/lib/stores.ts
git commit -m "feat: add persisted activeUnit store"
```

(The type error from Step 2 is resolved by Task 3, committed next — this is a two-commit unit by design so each file's diff stays reviewable on its own.)

---

### Task 3: Rewrite `api.ts` for the unit-scoped backend

**Files:**
- Modify: `frontend/src/lib/api.ts`

**Interfaces:**
- Produces: `UserResponse { id, first_name, last_name, email }`, `UnitResponse { id, code, name }`, `UnitMeResponse { unit_id, role, is_new_student, delivery_mode, skills, time_preferences }`, `UnitMembershipResponse { user_id, unit_id, role }`, `GroupResponse { id, preference_code, unit_id, creator_user_id, is_public, members, status, common_time_slots }`, `GroupJoinResponse { valid, reason?, group? }`, and `api.{register, login, getMe, getMyUnits, joinUnit, createUnit, getMyUnitProfile, updateMyUnitProfile, setMemberRole, createGroup, joinGroup, getMyGroups, getRecommendedTimes, leaveGroup}` — every page task below calls these exact method names/signatures.

- [x] **Step 1: Verify backend paths first**

Run: `cd backend && uv run fastapi dev src/main.py` (leave it running), then open `http://localhost:8000/docs` and confirm these operations exist exactly: `POST /auth/register`, `POST /auth/login`, `GET /users/me`, `GET /units/me`, `POST /units/join`, `POST /units/create`, `GET /units/{unit_id}/me`, `PATCH /units/{unit_id}/me`, `PATCH /units/{unit_id}/members/{email}`, `POST /groups/create`, `POST /groups/join`, `GET /groups/my-groups`, `GET /groups/{unit_id}/{group_id}/recommended-times`, `DELETE /groups/{unit_id}/{group_id}/leave`. Expected: all present (this plan was written against `backend/src/routers/{auth,users,units,groups}.py` as of the `unit-owned-groups-ui` branch — this step catches drift if the backend has changed since).

- [x] **Step 2: Replace `api.ts`**

Replace the full contents of `frontend/src/lib/api.ts` with:

```ts
const BASE = 'http://localhost:8000';

function authHeaders(): Record<string, string> {
	const token = typeof localStorage !== 'undefined' ? localStorage.getItem('token') : null;
	return token ? { Authorization: `Bearer ${token}` } : {};
}

async function req<T>(method: string, path: string, body?: unknown): Promise<T> {
	const headers: Record<string, string> = {
		'Content-Type': 'application/json',
		...authHeaders()
	};
	const res = await fetch(`${BASE}${path}`, {
		method,
		headers,
		body: body !== undefined ? JSON.stringify(body) : undefined
	});
	if (res.status === 204) return null as T;
	const data = await res.json();
	if (!res.ok) throw new Error(data.detail || 'Request failed');
	return data as T;
}

export interface UserResponse {
	id: number;
	first_name: string;
	last_name: string;
	email: string;
}

export interface TokenResponse {
	access_token: string;
	token_type: string;
}

export interface UnitResponse {
	id: number;
	code: string;
	name: string | null;
}

export interface UnitMeResponse {
	unit_id: number;
	role: string;
	is_new_student: boolean;
	delivery_mode: string | null;
	skills: string | null;
	time_preferences: string[];
}

export interface UnitMembershipResponse {
	user_id: number;
	unit_id: number;
	role: string;
}

export interface GroupResponse {
	id: number;
	preference_code: string | null;
	unit_id: number;
	creator_user_id: number | null;
	is_public: boolean;
	members: UserResponse[];
	status: 'valid' | 'provisional';
	common_time_slots: string[];
}

export interface GroupJoinResponse {
	valid: boolean;
	reason?: string;
	group?: GroupResponse;
}

export const api = {
	register: (data: { first_name: string; last_name: string; email: string; password: string }) =>
		req<UserResponse>('POST', '/auth/register', data),
	login: (email: string, password: string) =>
		req<TokenResponse>('POST', '/auth/login', { email, password }),
	getMe: () => req<UserResponse>('GET', '/users/me'),

	getMyUnits: () => req<UnitResponse[]>('GET', '/units/me'),
	joinUnit: (code: string) => req<UnitResponse>('POST', '/units/join', { code }),
	createUnit: (name?: string) => req<UnitResponse>('POST', '/units/create', { name }),
	getMyUnitProfile: (unitId: number) => req<UnitMeResponse>('GET', `/units/${unitId}/me`),
	updateMyUnitProfile: (
		unitId: number,
		data: Partial<{
			is_new_student: boolean;
			delivery_mode: string;
			skills: string;
			time_preferences: string[];
		}>
	) => req<UnitMeResponse>('PATCH', `/units/${unitId}/me`, data),
	setMemberRole: (unitId: number, email: string, role: 'administrator' | 'student') =>
		req<UnitMembershipResponse>(
			'PATCH',
			`/units/${unitId}/members/${encodeURIComponent(email)}`,
			{ role }
		),

	createGroup: (unitId: number, isPublic: boolean) =>
		req<GroupResponse>('POST', '/groups/create', { unit_id: unitId, is_public: isPublic }),
	joinGroup: (preferenceCode: string) =>
		req<GroupJoinResponse>('POST', '/groups/join', { preference_code: preferenceCode }),
	getMyGroups: () => req<GroupResponse[]>('GET', '/groups/my-groups'),
	getRecommendedTimes: (unitId: number, groupId: number) =>
		req<string[]>('GET', `/groups/${unitId}/${groupId}/recommended-times`),
	leaveGroup: (unitId: number, groupId: number) =>
		req<null>('DELETE', `/groups/${unitId}/${groupId}/leave`)
};
```

- [x] **Step 3: Type/compile check**

Run: `cd frontend && npm run check`
Expected: FAILS — the existing (not-yet-rewritten) `+page.svelte` files for `/`, `/register`, `/profile`, `/group` still reference old fields (`is_new_student` on register, `group_id` on `UserResponse`, `api.getMyGroup`, etc.) that no longer exist. This is expected; each page is fixed in its own task below. Confirm the errors are all in `src/routes/**/+page.svelte` and not in `stores.ts` (Task 2's error should now be gone) or `api.ts` itself.

- [x] **Step 4: Commit**

```bash
git add frontend/src/lib/api.ts
git commit -m "feat: rewrite api client for unit-scoped backend model"
```

---

### Task 4: `StatusPill` component

**Files:**
- Create: `frontend/src/lib/components/StatusPill.svelte`

**Interfaces:**
- Produces: `StatusPill` component, prop `status: 'complete' | 'incomplete' | 'pending'`, optional `label?: string`. Exported type `Status`. Consumed by the Explore page (Task 18).

- [x] **Step 1: Write the component**

```svelte
<script module lang="ts">
	export type Status = 'complete' | 'incomplete' | 'pending';
</script>

<script lang="ts">
	let { status, label }: { status: Status; label?: string } = $props();

	const badgeClass: Record<Status, string> = {
		complete: 'badge-success',
		pending: 'badge-warning',
		incomplete: 'badge-error'
	};

	const defaultLabel: Record<Status, string> = {
		complete: 'Complete',
		pending: 'Pending',
		incomplete: 'Incomplete'
	};
</script>

<span class="badge {badgeClass[status]} font-semibold">
	{label ?? defaultLabel[status]}
</span>
```

- [x] **Step 2: Type/compile check**

Run: `cd frontend && npm run check`
Expected: no new errors introduced by this file (the pre-existing route errors from Task 3 remain until their own tasks).

- [x] **Step 3: Commit**

```bash
git add frontend/src/lib/components/StatusPill.svelte
git commit -m "feat: add StatusPill component"
```

---

### Task 5: `PageHeader` component

**Files:**
- Create: `frontend/src/lib/components/PageHeader.svelte`

**Interfaces:**
- Produces: `PageHeader` component, props `title: string`, `subtitle?: string`, optional `actions?: Snippet` slot for right-aligned buttons. Consumed by Home, Explore, Group, Profile pages (Tasks 17-20).

- [x] **Step 1: Write the component**

```svelte
<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		title,
		subtitle,
		actions
	}: { title: string; subtitle?: string; actions?: Snippet } = $props();
</script>

<div class="bg-primary text-primary-content rounded-b-2xl px-6 py-5 flex items-center justify-between gap-4">
	<div>
		<h1 class="text-2xl font-extrabold tracking-tight">{title}</h1>
		{#if subtitle}
			<p class="text-primary-content/70 text-sm mt-1">{subtitle}</p>
		{/if}
	</div>
	{#if actions}
		<div class="flex items-center gap-2">
			{@render actions()}
		</div>
	{/if}
</div>
```

- [x] **Step 2: Type/compile check**

Run: `cd frontend && npm run check`
Expected: no new errors from this file.

- [x] **Step 3: Commit**

```bash
git add frontend/src/lib/components/PageHeader.svelte
git commit -m "feat: add PageHeader component"
```

---

### Task 6: `SectionCard` component

**Files:**
- Create: `frontend/src/lib/components/SectionCard.svelte`

**Interfaces:**
- Produces: `SectionCard` component, props `title?: string`, `children: Snippet`. Consumed by Home, Group, Profile pages.

- [x] **Step 1: Write the component**

```svelte
<script lang="ts">
	import type { Snippet } from 'svelte';

	let { title, children }: { title?: string; children: Snippet } = $props();
</script>

<div class="card bg-base-100 shadow-sm rounded-2xl">
	<div class="card-body">
		{#if title}
			<h2 class="font-bold text-lg mb-2">{title}</h2>
		{/if}
		{@render children()}
	</div>
</div>
```

- [x] **Step 2: Type/compile check**

Run: `cd frontend && npm run check`
Expected: no new errors from this file.

- [x] **Step 3: Commit**

```bash
git add frontend/src/lib/components/SectionCard.svelte
git commit -m "feat: add SectionCard component"
```

---

### Task 7: `TimeGrid` component

**Files:**
- Create: `frontend/src/lib/components/TimeGrid.svelte`

**Interfaces:**
- Consumes: `DAYS`, `PERIODS` from `$lib/timeslots` (existing, unchanged: 5 days × `Morning`/`Afternoon`/`Evening`, slot key `${day}${period}`, e.g. `mondayMorning`).
- Produces: `TimeGrid` component, props `selected: Set<string>`, `readonly?: boolean` (default `false`), `onToggle?: (slot: string) => void`. Consumed by Unit Setup, Group, Profile pages.

- [x] **Step 1: Write the component**

```svelte
<script lang="ts">
	import { DAYS, PERIODS } from '$lib/timeslots';

	let {
		selected,
		readonly = false,
		onToggle
	}: { selected: Set<string>; readonly?: boolean; onToggle?: (slot: string) => void } = $props();

	function dayLabel(day: string): string {
		return day.charAt(0).toUpperCase() + day.slice(1);
	}
</script>

<table class="table table-sm">
	<thead>
		<tr>
			<th></th>
			{#each PERIODS as period}
				<th class="text-center font-medium text-base-content/60">{period}</th>
			{/each}
		</tr>
	</thead>
	<tbody>
		{#each DAYS as day}
			<tr>
				<td class="text-sm text-base-content/70 pr-4">{dayLabel(day)}</td>
				{#each PERIODS as period}
					{@const slot = `${day}${period}`}
					<td class="text-center">
						{#if readonly}
							<span
								class="text-sm {selected.has(slot)
									? 'text-primary font-semibold'
									: 'text-base-content/20'}"
							>
								{selected.has(slot) ? '✓' : '·'}
							</span>
						{:else}
							<input
								type="checkbox"
								class="checkbox checkbox-sm checkbox-primary"
								checked={selected.has(slot)}
								onchange={() => onToggle?.(slot)}
							/>
						{/if}
					</td>
				{/each}
			</tr>
		{/each}
	</tbody>
</table>
```

- [x] **Step 2: Type/compile check**

Run: `cd frontend && npm run check`
Expected: no new errors from this file.

- [x] **Step 3: Commit**

```bash
git add frontend/src/lib/components/TimeGrid.svelte
git commit -m "feat: add TimeGrid component"
```

---

### Task 8: `CountdownTimer` component

**Files:**
- Create: `frontend/src/lib/components/CountdownTimer.svelte`

**Interfaces:**
- Produces: `CountdownTimer` component, prop `targetDate: string` (ISO datetime). Consumed by Home page (Task 17).

- [x] **Step 1: Write the component**

```svelte
<script lang="ts">
	import { onMount } from 'svelte';

	let { targetDate }: { targetDate: string } = $props();

	let days = $state(0);
	let hours = $state(0);
	let minutes = $state(0);

	function update() {
		const diff = Math.max(0, new Date(targetDate).getTime() - Date.now());
		const totalMinutes = Math.floor(diff / 60000);
		days = Math.floor(totalMinutes / (60 * 24));
		hours = Math.floor((totalMinutes % (60 * 24)) / 60);
		minutes = totalMinutes % 60;
	}

	onMount(() => {
		update();
		const interval = setInterval(update, 60000);
		return () => clearInterval(interval);
	});

	const units = $derived([
		[days, 'days'],
		[hours, 'hours'],
		[minutes, 'minutes']
	] as const);
</script>

<div class="flex gap-3 justify-center">
	{#each units as [value, label]}
		<div class="flex flex-col items-center">
			<div
				class="bg-primary text-primary-content rounded-lg w-12 h-12 flex items-center justify-center text-lg font-bold"
			>
				{String(value).padStart(2, '0')}
			</div>
			<span class="text-xs text-base-content/60 mt-1">{label}</span>
		</div>
	{/each}
</div>
```

- [x] **Step 2: Type/compile check**

Run: `cd frontend && npm run check`
Expected: no new errors from this file.

- [x] **Step 3: Commit**

```bash
git add frontend/src/lib/components/CountdownTimer.svelte
git commit -m "feat: add CountdownTimer component"
```

---

### Task 9: `StatDonut` component

**Files:**
- Create: `frontend/src/lib/components/StatDonut.svelte`

**Interfaces:**
- Produces: `StatDonut` component, props `value: number`, `total: number`, `label: string`. Consumed by Home page (Task 17). Renders a real percentage (`value / total`) as a pie-slice arc — not decorative. `total` has no real backend source yet (see `docs/backlog.md`, "Unit enrollment total for StatDonut"); callers pass a placeholder constant until that field exists.

- [x] **Step 1: Write the component**

```svelte
<script lang="ts">
	let { value, total, label }: { value: number; total: number; label: string } = $props();

	// TODO: `total` has no real backend source yet — Unit has no enrollment/
	// capacity field. See docs/backlog.md, "Unit enrollment total for StatDonut".
	// Callers currently pass a placeholder constant until that field exists.

	const percent = $derived(total > 0 ? Math.min(1, Math.max(0, value / total)) : 0);

	function polarToCartesian(angleDeg: number) {
		const angleRad = ((angleDeg - 90) * Math.PI) / 180;
		return { x: 50 + 45 * Math.cos(angleRad), y: 50 + 45 * Math.sin(angleRad) };
	}

	const arcPath = $derived.by(() => {
		if (percent <= 0) return '';
		const angle = percent * 360;
		const start = polarToCartesian(0);
		const end = polarToCartesian(angle);
		const largeArcFlag = percent > 0.5 ? 1 : 0;
		return `M50,50 L${start.x},${start.y} A45,45 0 ${largeArcFlag} 1 ${end.x},${end.y} Z`;
	});
</script>

<div class="flex flex-col items-center gap-2">
	<svg width="96" height="96" viewBox="0 0 100 100" aria-hidden="true">
		<circle cx="50" cy="50" r="45" fill="var(--color-base-200)" />
		{#if percent >= 1}
			<circle cx="50" cy="50" r="45" fill="var(--color-accent)" />
		{:else if arcPath}
			<path d={arcPath} fill="var(--color-accent)" />
		{/if}
	</svg>
	<p class="text-center">
		<span class="text-2xl font-extrabold text-primary">{value}</span>
		<span class="block text-sm text-base-content/70">{label}</span>
	</p>
</div>
```

- [x] **Step 2: Type/compile check + visual check**

Run: `cd frontend && npm run check`. Then in a scratch route or via Storybook-free manual check (it'll be visible for real once Task 17 wires it into Home) — for now just confirm no type errors.
Expected: no new errors from this file.

- [x] **Step 3: Commit**

```bash
git add frontend/src/lib/components/StatDonut.svelte
git commit -m "feat: add StatDonut component"
```

---

### Task 10: `UnitSwitcher` component

**Files:**
- Create: `frontend/src/lib/components/UnitSwitcher.svelte`

**Interfaces:**
- Consumes: `UnitResponse` type from `$lib/api`.
- Produces: `UnitSwitcher` component, props `units: UnitResponse[]`, `activeUnitId: number | null`, `onSwitch: (unit: UnitResponse) => void`. Consumed by the layout navbar (Task 11).

- [x] **Step 1: Write the component**

```svelte
<script lang="ts">
	import type { UnitResponse } from '$lib/api';

	let {
		units,
		activeUnitId,
		onSwitch
	}: {
		units: UnitResponse[];
		activeUnitId: number | null;
		onSwitch: (unit: UnitResponse) => void;
	} = $props();

	const activeUnit = $derived(units.find((u) => u.id === activeUnitId) ?? null);
</script>

<div class="dropdown">
	<div tabindex="0" role="button" class="btn btn-ghost btn-sm">
		{activeUnit ? (activeUnit.name ?? activeUnit.code) : 'Select unit'} ▾
	</div>
	<ul class="dropdown-content menu bg-base-100 text-base-content rounded-box shadow-sm z-10 w-52 p-2">
		{#each units as unit}
			<li>
				<button class:menu-active={unit.id === activeUnitId} onclick={() => onSwitch(unit)}>
					{unit.name ?? unit.code}
				</button>
			</li>
		{/each}
	</ul>
</div>
```

- [x] **Step 2: Type/compile check**

Run: `cd frontend && npm run check`
Expected: no new errors from this file.

- [x] **Step 3: Commit**

```bash
git add frontend/src/lib/components/UnitSwitcher.svelte
git commit -m "feat: add UnitSwitcher component"
```

---

### Task 11: Rewrite the layout/navbar

**Files:**
- Modify: `frontend/src/routes/+layout.svelte`

**Interfaces:**
- Consumes: `token`, `user`, `activeUnit` stores (`$lib/stores`); `api.getMe`, `api.getMyUnits` (`$lib/api`); `UnitSwitcher` (Task 10).
- Produces: the app shell every route renders inside. No other task depends on new exports from this file (it's a leaf in the dependency graph, but everything visually sits inside it).

- [x] **Step 1: Rewrite the layout**

Replace the full contents of `frontend/src/routes/+layout.svelte` with:

```svelte
<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { token, user, activeUnit } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { api, type UnitResponse } from '$lib/api';
	import UnitSwitcher from '$lib/components/UnitSwitcher.svelte';
	import type { Snippet } from 'svelte';

	let { children }: { children: Snippet } = $props();

	let myUnits = $state<UnitResponse[]>([]);

	onMount(async () => {
		if (!$token) return;
		if (!$user) {
			try {
				$user = await api.getMe();
			} catch {
				token.clear();
				goto('/');
				return;
			}
		}
		myUnits = await api.getMyUnits();
	});

	function logout() {
		token.clear();
		user.set(null);
		activeUnit.clear();
		goto('/');
	}

	function switchUnit(unit: UnitResponse) {
		activeUnit.set(unit);
		goto('/home');
	}
</script>

{#if $token}
	<div class="navbar bg-primary text-primary-content px-4">
		<div class="navbar-start gap-2">
			<span class="font-extrabold text-lg">TeamUp!</span>
			<UnitSwitcher units={myUnits} activeUnitId={$activeUnit?.id ?? null} onSwitch={switchUnit} />
		</div>
		<div class="navbar-center gap-1">
			<a
				href="/home"
				class="btn btn-ghost btn-sm"
				class:btn-active={$page.url.pathname === '/home'}
			>
				Home
			</a>
			<a
				href="/explore"
				class="btn btn-ghost btn-sm"
				class:btn-active={$page.url.pathname === '/explore'}
			>
				Explore
			</a>
			<a
				href="/group"
				class="btn btn-ghost btn-sm"
				class:btn-active={$page.url.pathname === '/group'}
			>
				Group
			</a>
			<a
				href="/profile"
				class="btn btn-ghost btn-sm"
				class:btn-active={$page.url.pathname === '/profile'}
			>
				Profile
			</a>
		</div>
		<div class="navbar-end">
			<button class="btn btn-ghost btn-sm" onclick={logout}>Logout</button>
		</div>
	</div>
{/if}

{@render children()}
```

- [x] **Step 2: Type/compile check**

Run: `cd frontend && npm run check`
Expected: the route-level errors from Task 3 still show (routes not yet rewritten); no *new* errors from `+layout.svelte` itself.

- [x] **Step 3: Commit**

```bash
git add frontend/src/routes/+layout.svelte
git commit -m "feat: rewrite navbar with unit switcher"
```

---

### Task 12: Rewrite Sign In (`/`)

**Files:**
- Modify: `frontend/src/routes/+page.svelte`

**Interfaces:**
- Consumes: `api.login`, `api.getMe`, `api.getMyUnits` (`$lib/api`); `token`, `user`, `activeUnit` stores.

- [x] **Step 1: Rewrite the page**

Replace the full contents of `frontend/src/routes/+page.svelte` with:

```svelte
<script lang="ts">
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { token, user, activeUnit } from '$lib/stores';

	let email = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	onMount(() => {
		if ($token) goto('/home');
	});

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		loading = true;
		try {
			const data = await api.login(email, password);
			token.set(data.access_token);
			user.set(await api.getMe());

			const units = await api.getMyUnits();
			if (units.length === 0) {
				goto('/onboarding/unit');
				return;
			}
			const current = get(activeUnit);
			const stillValid = current && units.some((u) => u.id === current.id);
			activeUnit.set(stillValid ? current : units[0]);
			goto('/home');
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Login failed';
		} finally {
			loading = false;
		}
	}
</script>

<div class="min-h-screen flex items-center justify-center px-4">
	<div class="card bg-base-100 shadow-sm rounded-2xl w-full max-w-sm">
		<div class="card-body">
			<h1 class="text-2xl font-extrabold text-primary mb-1">Sign In</h1>
			<p class="text-sm text-base-content/60 mb-4">Welcome back to TeamUp!</p>
			<form onsubmit={handleSubmit} class="flex flex-col gap-3">
				<label class="flex flex-col gap-1">
					<span class="text-sm font-medium">Email</span>
					<input type="email" class="input input-bordered" bind:value={email} required />
				</label>
				<label class="flex flex-col gap-1">
					<span class="text-sm font-medium">Password</span>
					<input type="password" class="input input-bordered" bind:value={password} required />
				</label>
				{#if error}
					<p class="text-error text-sm">{error}</p>
				{/if}
				<button type="submit" class="btn btn-primary mt-1" disabled={loading}>
					{loading ? 'Signing in…' : 'Sign In'}
				</button>
			</form>
			<p class="text-sm text-base-content/60 mt-3">
				No account? <a href="/register" class="link">Register</a>
			</p>
		</div>
	</div>
</div>
```

- [x] **Step 2: Type/compile check**

Run: `cd frontend && npm run check`
Expected: this file's prior errors are gone; remaining errors are only in `/register`, `/profile`, `/group` (not yet rewritten).

- [x] **Step 3: Manual check**

With the backend running (`cd backend && uv run fastapi dev src/main.py`) and frontend running (`cd frontend && npm run dev`), log in with an existing test account. Expected: redirected to `/onboarding/unit` if the account has no units, or `/home` (404 for now — built in Task 17) if it does.

- [x] **Step 4: Commit**

```bash
git add frontend/src/routes/+page.svelte
git commit -m "feat: restyle sign-in and route by unit membership"
```

---

### Task 13: Rewrite Register (`/register`)

**Files:**
- Modify: `frontend/src/routes/register/+page.svelte`

**Interfaces:**
- Consumes: `api.register`, `api.login` (`$lib/api`); `token` store.

- [x] **Step 1: Rewrite the page**

Replace the full contents of `frontend/src/routes/register/+page.svelte` with:

```svelte
<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { token } from '$lib/stores';

	let firstName = $state('');
	let lastName = $state('');
	let email = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	onMount(() => {
		if ($token) goto('/home');
	});

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		loading = true;
		try {
			await api.register({ first_name: firstName, last_name: lastName, email, password });
			const loginData = await api.login(email, password);
			token.set(loginData.access_token);
			goto('/onboarding/unit');
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Registration failed';
		} finally {
			loading = false;
		}
	}
</script>

<div class="min-h-screen flex items-center justify-center px-4">
	<div class="card bg-base-100 shadow-sm rounded-2xl w-full max-w-md">
		<div class="card-body">
			<h1 class="text-2xl font-extrabold text-primary mb-1">Register an Account</h1>
			<p class="text-sm text-base-content/60 mb-4">
				Please fill out the following form to register with TeamUp.
			</p>
			<form onsubmit={handleSubmit} class="flex flex-col gap-3">
				<div class="grid grid-cols-2 gap-3">
					<label class="flex flex-col gap-1">
						<span class="text-sm font-medium">First Name</span>
						<input type="text" class="input input-bordered" bind:value={firstName} required />
					</label>
					<label class="flex flex-col gap-1">
						<span class="text-sm font-medium">Last Name</span>
						<input type="text" class="input input-bordered" bind:value={lastName} required />
					</label>
				</div>
				<label class="flex flex-col gap-1">
					<span class="text-sm font-medium">Email</span>
					<input type="email" class="input input-bordered" bind:value={email} required />
				</label>
				<label class="flex flex-col gap-1">
					<span class="text-sm font-medium">Password</span>
					<input type="password" class="input input-bordered" bind:value={password} required />
				</label>
				{#if error}
					<p class="text-error text-sm">{error}</p>
				{/if}
				<button type="submit" class="btn btn-primary mt-1" disabled={loading}>
					{loading ? 'Registering…' : 'Register'}
				</button>
			</form>
			<p class="text-sm text-base-content/60 mt-3">
				Already have an account? <a href="/" class="link">Sign In</a>
			</p>
		</div>
	</div>
</div>
```

- [x] **Step 2: Type/compile check**

Run: `cd frontend && npm run check`
Expected: this file's prior errors are gone; remaining errors only in `/profile`, `/group`.

- [x] **Step 3: Manual check**

Register a brand-new account in the browser. Expected: redirected to `/onboarding/unit` (404 for now — built next task).

- [x] **Step 4: Commit**

```bash
git add frontend/src/routes/register/+page.svelte
git commit -m "feat: rewrite register as account-only form"
```

---

### Task 14: Join/Create Unit page (`/onboarding/unit`)

**Files:**
- Create: `frontend/src/routes/onboarding/unit/+page.svelte`

**Interfaces:**
- Consumes: `api.joinUnit`, `api.createUnit` (`$lib/api`); `token`, `activeUnit` stores.

- [x] **Step 1: Write the page**

```svelte
<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { token, activeUnit } from '$lib/stores';

	let mode = $state<'join' | 'create'>('join');
	let code = $state('');
	let unitName = $state('');
	let error = $state('');
	let loading = $state(false);

	onMount(() => {
		if (!$token) goto('/');
	});

	async function handleJoin(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		loading = true;
		try {
			const unit = await api.joinUnit(code);
			activeUnit.set(unit);
			goto('/onboarding/setup');
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Could not join unit';
		} finally {
			loading = false;
		}
	}

	async function handleCreate(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		loading = true;
		try {
			const unit = await api.createUnit(unitName || undefined);
			activeUnit.set(unit);
			goto('/onboarding/setup');
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Could not create unit';
		} finally {
			loading = false;
		}
	}
</script>

<div class="min-h-screen flex items-center justify-center px-4">
	<div class="card bg-base-100 shadow-sm rounded-2xl w-full max-w-md">
		<div class="card-body">
			<h1 class="text-2xl font-extrabold text-primary mb-1">Join or Create a Unit</h1>
			<p class="text-sm text-base-content/60 mb-4">
				Enter a unit code to join, or create a new unit.
			</p>

			<div role="tablist" class="tabs tabs-boxed mb-4">
				<button
					type="button"
					role="tab"
					class="tab {mode === 'join' ? 'tab-active' : ''}"
					onclick={() => (mode = 'join')}
				>
					Join a Unit
				</button>
				<button
					type="button"
					role="tab"
					class="tab {mode === 'create' ? 'tab-active' : ''}"
					onclick={() => (mode = 'create')}
				>
					Create a Unit
				</button>
			</div>

			{#if mode === 'join'}
				<form onsubmit={handleJoin} class="flex flex-col gap-3">
					<label class="flex flex-col gap-1">
						<span class="text-sm font-medium">Unit Code</span>
						<input
							type="text"
							class="input input-bordered"
							bind:value={code}
							placeholder="e.g. IFB398"
							required
						/>
					</label>
					{#if error}<p class="text-error text-sm">{error}</p>{/if}
					<button type="submit" class="btn btn-primary mt-1" disabled={loading}>
						{loading ? 'Joining…' : 'Join Unit'}
					</button>
				</form>
			{:else}
				<form onsubmit={handleCreate} class="flex flex-col gap-3">
					<label class="flex flex-col gap-1">
						<span class="text-sm font-medium"
							>Unit Name <span class="text-base-content/50 font-normal">(optional)</span></span
						>
						<input
							type="text"
							class="input input-bordered"
							bind:value={unitName}
							placeholder="e.g. IFB398 Capstone"
						/>
					</label>
					{#if error}<p class="text-error text-sm">{error}</p>{/if}
					<button type="submit" class="btn btn-primary mt-1" disabled={loading}>
						{loading ? 'Creating…' : 'Create Unit'}
					</button>
				</form>
			{/if}
		</div>
	</div>
</div>
```

- [x] **Step 2: Type/compile check**

Run: `cd frontend && npm run check`
Expected: no new errors from this file.

- [x] **Step 3: Manual check**

From a logged-in account with zero units, use "Create a Unit". Expected: redirected to `/onboarding/setup` (404 for now — built next task). Confirm in `http://localhost:8000/docs` (or a second browser tab hitting `GET /units/me` with the token) that the unit was actually created server-side.

- [x] **Step 4: Commit**

```bash
git add frontend/src/routes/onboarding/unit/+page.svelte
git commit -m "feat: add join/create unit onboarding page"
```

---

### Task 15: Unit Setup page (`/onboarding/setup`)

**Files:**
- Create: `frontend/src/routes/onboarding/setup/+page.svelte`

**Interfaces:**
- Consumes: `api.updateMyUnitProfile` (`$lib/api`); `token`, `activeUnit` stores; `TimeGrid` (Task 7).

- [x] **Step 1: Write the page**

```svelte
<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { token, activeUnit } from '$lib/stores';
	import TimeGrid from '$lib/components/TimeGrid.svelte';

	let deliveryMode = $state('Online');
	let skills = $state('');
	let selectedSlots = $state(new Set<string>());
	let error = $state('');
	let loading = $state(false);

	onMount(() => {
		if (!$token) {
			goto('/');
			return;
		}
		if (!$activeUnit) {
			goto('/onboarding/unit');
		}
	});

	function toggleSlot(slot: string) {
		const next = new Set(selectedSlots);
		if (next.has(slot)) next.delete(slot);
		else next.add(slot);
		selectedSlots = next;
	}

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		if (!$activeUnit) return;
		error = '';
		loading = true;
		try {
			await api.updateMyUnitProfile($activeUnit.id, {
				delivery_mode: deliveryMode,
				skills: skills || undefined,
				time_preferences: [...selectedSlots]
			});
			goto('/home');
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Could not save your details';
		} finally {
			loading = false;
		}
	}
</script>

<div class="min-h-screen flex items-center justify-center px-4 py-10">
	<div class="card bg-base-100 shadow-sm rounded-2xl w-full max-w-xl">
		<div class="card-body">
			<h1 class="text-2xl font-extrabold text-primary mb-1">Set Up Your Profile</h1>
			<p class="text-sm text-base-content/60 mb-4">
				Tell {$activeUnit?.name ?? $activeUnit?.code} a bit about how you'll be studying.
			</p>
			<form onsubmit={handleSubmit} class="flex flex-col gap-4">
				<div class="flex flex-col gap-2">
					<span class="text-sm font-medium">Delivery Mode</span>
					<div class="flex gap-6">
						<label class="flex items-center gap-2 text-sm cursor-pointer">
							<input type="radio" class="radio radio-sm" bind:group={deliveryMode} value="Online" />
							Online
						</label>
						<label class="flex items-center gap-2 text-sm cursor-pointer">
							<input
								type="radio"
								class="radio radio-sm"
								bind:group={deliveryMode}
								value="In-person"
							/>
							In-person
						</label>
					</div>
				</div>

				<label class="flex flex-col gap-1">
					<span class="text-sm font-medium">
						Skills <span class="text-base-content/50 font-normal">(optional)</span>
					</span>
					<input
						type="text"
						class="input input-bordered"
						bind:value={skills}
						placeholder="e.g. Python, React, UI Design"
					/>
				</label>

				<div class="flex flex-col gap-2">
					<span class="text-sm font-medium">Availability</span>
					<TimeGrid selected={selectedSlots} onToggle={toggleSlot} />
				</div>

				<!--
					TODO: admin-defined per-unit questions would render here once a
					custom-question backend feature exists (see docs/superpowers/specs/
					2026-08-08-frontend-ui-rework-design.md, Non-goals). No component yet —
					this comment is the intended insertion point.
				-->

				{#if error}<p class="text-error text-sm">{error}</p>{/if}

				<button type="submit" class="btn btn-primary mt-1" disabled={loading}>
					{loading ? 'Saving…' : 'Finish Setup'}
				</button>
			</form>
		</div>
	</div>
</div>
```

- [x] **Step 2: Type/compile check**

Run: `cd frontend && npm run check`
Expected: no new errors from this file.

- [x] **Step 3: Manual check**

Complete the form after joining/creating a unit. Expected: redirected to `/home` (404 for now — built in Task 17); `GET /units/{id}/me` (via `/docs`) shows the saved delivery mode/skills/time preferences.

- [x] **Step 4: Commit**

```bash
git add frontend/src/routes/onboarding/setup/+page.svelte
git commit -m "feat: add unit setup onboarding page"
```

---

### Task 16: Mock student directory data

**Files:**
- Create: `frontend/src/lib/mockStudents.ts`

**Interfaces:**
- Produces: `MockStudent { id, name, degree, skills, status, email }` and `mockStudents: MockStudent[]`. Consumed by Home (Task 17, for the registered-count stat) and Explore (Task 18).

- [x] **Step 1: Write the mock data**

```ts
// Mocked student directory data. No backend endpoint exists to list a unit's
// students with degree/skills/group-completion status (see design spec
// docs/superpowers/specs/2026-08-08-frontend-ui-rework-design.md, Non-goals).
// Replace this module with a real API call once that endpoint exists.

export interface MockStudent {
	id: number;
	name: string;
	degree: string;
	skills: string;
	status: 'complete' | 'incomplete' | 'pending';
	email: string;
}

export const mockStudents: MockStudent[] = [
	{
		id: 1,
		name: 'Isabelle Dayman',
		degree: 'Computer Science',
		skills: 'React, Figma',
		status: 'complete',
		email: 'isabelle.dayman@example.com'
	},
	{
		id: 2,
		name: 'George Grigman',
		degree: 'Computer Science',
		skills: 'Python, SQL',
		status: 'pending',
		email: 'george.grigman@example.com'
	},
	{
		id: 3,
		name: 'Johnny Davis',
		degree: 'Information Systems',
		skills: 'Java',
		status: 'incomplete',
		email: 'johnny.davis@example.com'
	},
	{
		id: 4,
		name: 'Leila Crickey',
		degree: 'Computer Science',
		skills: 'UI Design',
		status: 'complete',
		email: 'leila.crickey@example.com'
	},
	{
		id: 5,
		name: 'Frida Columbus',
		degree: 'Information Technology',
		skills: 'Node.js',
		status: 'pending',
		email: 'frida.columbus@example.com'
	}
];
```

- [x] **Step 2: Type/compile check**

Run: `cd frontend && npm run check`
Expected: no new errors from this file.

- [x] **Step 3: Commit**

```bash
git add frontend/src/lib/mockStudents.ts
git commit -m "feat: add mocked student directory data"
```

---

### Task 17: Home dashboard (`/home`)

**Files:**
- Create: `frontend/src/routes/home/+page.svelte`

**Interfaces:**
- Consumes: `token`, `user`, `activeUnit` stores; `mockStudents` (Task 16); `PageHeader` (Task 5), `SectionCard` (Task 6), `CountdownTimer` (Task 8), `StatDonut` (Task 9).

- [x] **Step 1: Write the page**

```svelte
<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { token, user, activeUnit } from '$lib/stores';
	import { mockStudents } from '$lib/mockStudents';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import SectionCard from '$lib/components/SectionCard.svelte';
	import CountdownTimer from '$lib/components/CountdownTimer.svelte';
	import StatDonut from '$lib/components/StatDonut.svelte';

	// Placeholder due date — no due_date field exists on Unit yet (see design
	// spec Non-goals). Replace with a real per-unit value if that field is added.
	const GROUPINGS_DUE = '2026-09-15T00:00:00';

	// TODO: placeholder enrollment total — Unit has no capacity/enrollment
	// field yet (see docs/backlog.md, "Unit enrollment total for StatDonut").
	// Replace with a real per-unit value once that field exists.
	const EXPECTED_ENROLLMENT = 200;

	onMount(() => {
		if (!$token) {
			goto('/');
			return;
		}
		if (!$activeUnit) {
			goto('/onboarding/unit');
		}
	});
</script>

{#if $activeUnit}
	<PageHeader
		title={`Welcome, ${$user?.first_name ?? ''}!`}
		subtitle={$activeUnit.name ?? $activeUnit.code}
	/>

	<div class="max-w-3xl mx-auto px-4 py-8 grid gap-4 md:grid-cols-2">
		<div class="flex flex-col gap-3">
			<a href="/group" class="btn btn-primary btn-block">Create a Group</a>
			<a href="/explore" class="btn btn-outline btn-block">Explore Students & Groups</a>
		</div>

		<SectionCard>
			<StatDonut
				value={mockStudents.length}
				total={EXPECTED_ENROLLMENT}
				label="students have registered in TeamUp!"
			/>
		</SectionCard>

		<div class="md:col-span-2">
			<SectionCard title="Initial groupings are due">
				<CountdownTimer targetDate={GROUPINGS_DUE} />
			</SectionCard>
		</div>
	</div>
{/if}
```

- [x] **Step 2: Type/compile check**

Run: `cd frontend && npm run check`
Expected: no new errors from this file.

- [x] **Step 3: Manual check**

Log in with a unit already set up. Expected: `/home` renders the header, the two action buttons, the donut stat with the mock count, and a live-updating countdown.

- [x] **Step 4: Commit**

```bash
git add frontend/src/routes/home/+page.svelte
git commit -m "feat: add home dashboard"
```

---

### Task 18: Explore Students & Groups page (`/explore`)

**Files:**
- Create: `frontend/src/routes/explore/+page.svelte`
- Modify: `frontend/src/lib/api.ts` (adds `getGroups`, not in the original Task 3 script)

**Interfaces:**
- Consumes: `api.getMyUnitProfile`, `api.setMemberRole` (`$lib/api`); `token`, `activeUnit` stores; `mockStudents`, `MockStudent` (Task 16); `PageHeader` (Task 5), `StatusPill` (Task 4).

**Scope note (deviation from the original script below, decided 2026-08-17):** while implementing this task, discovered `GET /groups/{unit_id}` (public groups + own groups, filtered by role) is a real, working backend endpoint that Task 3's `api.ts` never wired up — the design spec's Non-goals section only ruled out a *students* listing endpoint, not groups. Added `api.getGroups(unitId)` to `api.ts` and extended this page with a real "Public Groups" section (not in the script below): fetches `getGroups` + `getMyGroups` on mount, lets students join public groups via the existing real `api.joinGroup`, and shows a disabled Join button with a tooltip ("You're already enrolled in a different group for this unit") for any group you can't join because you're already in one for this unit. The student directory below is still fully mocked as originally planned — only the groups half was extended.

- [x] **Step 1: Write the page**

```svelte
<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { token, activeUnit } from '$lib/stores';
	import { api } from '$lib/api';
	import { mockStudents, type MockStudent } from '$lib/mockStudents';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import StatusPill from '$lib/components/StatusPill.svelte';

	// Explore is mocked: no backend endpoint lists a unit's students with degree/
	// skills/group status yet (see design spec Non-goals). The role-change call
	// below is real (PATCH /units/{id}/members/{email}) but is applied against
	// these mock rows' emails, which won't correspond to real unit members.

	let search = $state('');
	let degreeFilter = $state('All');
	let isOwner = $state(false);
	let roleUpdateError = $state('');

	const degrees = $derived(['All', ...new Set(mockStudents.map((s) => s.degree))]);

	const filtered = $derived(
		mockStudents.filter((s) => {
			const matchesSearch = s.name.toLowerCase().includes(search.toLowerCase());
			const matchesDegree = degreeFilter === 'All' || s.degree === degreeFilter;
			return matchesSearch && matchesDegree;
		})
	);

	onMount(async () => {
		if (!$token) {
			goto('/');
			return;
		}
		if (!$activeUnit) {
			goto('/onboarding/unit');
			return;
		}
		try {
			const profile = await api.getMyUnitProfile($activeUnit.id);
			isOwner = profile.role === 'owner';
		} catch {
			isOwner = false;
		}
	});

	async function changeRole(student: MockStudent, role: 'administrator' | 'student') {
		if (!$activeUnit) return;
		roleUpdateError = '';
		try {
			await api.setMemberRole($activeUnit.id, student.email, role);
		} catch (e: unknown) {
			roleUpdateError = e instanceof Error ? e.message : 'Could not update role';
		}
	}
</script>

<PageHeader
	title="Explore Students & Groups"
	subtitle={`Search for students and public groups in ${$activeUnit?.name ?? $activeUnit?.code ?? ''}`}
/>

<div class="max-w-3xl mx-auto px-4 py-8">
	<div class="flex gap-3 mb-4">
		<input
			type="text"
			class="input input-bordered flex-1"
			placeholder="Search for students"
			bind:value={search}
		/>
		<select class="select select-bordered" bind:value={degreeFilter}>
			{#each degrees as degree}
				<option value={degree}>{degree}</option>
			{/each}
		</select>
	</div>

	{#if roleUpdateError}<p class="text-error text-sm mb-2">{roleUpdateError}</p>{/if}

	<div class="flex flex-col gap-3">
		{#each filtered as student}
			<div class="card bg-base-100 shadow-sm rounded-2xl">
				<div class="card-body flex-row items-center justify-between">
					<div>
						<p class="font-bold">{student.name}</p>
						<p class="text-sm text-base-content/60">Degree: {student.degree}</p>
						<p class="text-sm text-base-content/60">Skills: {student.skills}</p>
					</div>
					<div class="flex items-center gap-3">
						<StatusPill status={student.status} />
						{#if isOwner}
							<select
								class="select select-bordered select-sm"
								onchange={(e) =>
									changeRole(student, e.currentTarget.value as 'administrator' | 'student')}
							>
								<option value="student">Student</option>
								<option value="administrator">Administrator</option>
							</select>
						{/if}
					</div>
				</div>
			</div>
		{/each}
	</div>
</div>
```

- [x] **Step 2: Type/compile check**

Run: `cd frontend && npm run check`
Expected: no new errors from this file.

- [x] **Step 3: Manual check**

Visit `/explore`. Expected: search box filters the mock list by name, the degree select filters by degree, each row shows a colored `StatusPill`. If logged in as a unit owner, a role `<select>` appears per row (changing it will 404/error against real emails unless you seed a matching real member — that's expected for mock data; confirm the *request* fires correctly via the Network tab, not that it succeeds). Additionally (scope extension): the Public Groups section loads real groups via `GET /groups/{unit_id}`; joining via `api.joinGroup` was verified end-to-end via curl (two real accounts, one created a public group, the other joined it, group status flipped `valid` → `provisional` correctly, and a second join attempt correctly 409s — matching the disabled/tooltip UI state).

- [x] **Step 4: Commit**

```bash
git add frontend/src/routes/explore/+page.svelte
git commit -m "feat: add explore students & groups page (mocked data)"
```

---

### Task 19: Rewrite Group page (`/group`)

**Files:**
- Modify: `frontend/src/routes/group/+page.svelte`

**Interfaces:**
- Consumes: `api.createGroup`, `api.joinGroup`, `api.getMyGroups`, `api.getRecommendedTimes`, `api.leaveGroup` (`$lib/api`); `token`, `activeUnit` stores; `formatSlot` (`$lib/timeslots`); `PageHeader` (Task 5), `SectionCard` (Task 6).

- [ ] **Step 1: Rewrite the page**

Replace the full contents of `frontend/src/routes/group/+page.svelte` with:

```svelte
<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api, type GroupResponse } from '$lib/api';
	import { token, activeUnit } from '$lib/stores';
	import { formatSlot } from '$lib/timeslots';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import SectionCard from '$lib/components/SectionCard.svelte';

	let loading = $state(true);
	let group = $state<GroupResponse | null>(null);
	let recommendedTimes = $state<string[]>([]);
	let joinCode = $state('');
	let isPublic = $state(false);
	let error = $state('');
	let successMsg = $state('');
	let creating = $state(false);
	let joining = $state(false);
	let leaving = $state(false);

	onMount(async () => {
		if (!$token) {
			goto('/');
			return;
		}
		if (!$activeUnit) {
			goto('/onboarding/unit');
			return;
		}
		await loadGroup();
		loading = false;
	});

	async function loadGroup() {
		if (!$activeUnit) return;
		const groups = await api.getMyGroups();
		group = groups.find((g) => g.unit_id === $activeUnit!.id) ?? null;
		if (group && group.status === 'provisional') {
			recommendedTimes = await api.getRecommendedTimes($activeUnit.id, group.id);
		} else {
			recommendedTimes = [];
		}
	}

	async function createGroup(e: SubmitEvent) {
		e.preventDefault();
		if (!$activeUnit) return;
		error = '';
		creating = true;
		try {
			group = await api.createGroup($activeUnit.id, isPublic);
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Failed to create group';
		} finally {
			creating = false;
		}
	}

	async function joinGroup(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		joining = true;
		try {
			const result = await api.joinGroup(joinCode);
			if (!result.valid || !result.group) {
				error = result.reason ?? 'Could not join group';
				return;
			}
			await loadGroup();
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Failed to join group';
		} finally {
			joining = false;
		}
	}

	async function leaveGroup() {
		if (!$activeUnit || !group) return;
		if (!confirm('Leave this group?')) return;
		error = '';
		leaving = true;
		try {
			await api.leaveGroup($activeUnit.id, group.id);
			group = null;
			recommendedTimes = [];
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Failed to leave group';
		} finally {
			leaving = false;
		}
	}

	function copyCode() {
		if (group?.preference_code) {
			navigator.clipboard.writeText(group.preference_code);
			successMsg = 'Invite code copied!';
		}
	}
</script>

<PageHeader title="My Group" subtitle={$activeUnit?.name ?? $activeUnit?.code} />

<div class="max-w-xl mx-auto px-4 py-8">
	{#if loading}
		<span class="loading loading-spinner"></span>
	{:else if !group}
		<SectionCard title="Create a Group">
			<form onsubmit={createGroup} class="flex flex-col gap-3 mb-6">
				<label class="flex flex-col gap-1">
					<span class="text-sm font-medium">Visibility</span>
					<select class="select select-bordered" bind:value={isPublic}>
						<option value={false}>Private — invite only</option>
						<option value={true}>Public — visible to the unit</option>
					</select>
				</label>
				{#if error}<p class="text-error text-sm">{error}</p>{/if}
				<button type="submit" class="btn btn-primary" disabled={creating}>
					{creating ? 'Creating…' : 'Create Group'}
				</button>
			</form>

			<div class="divider">or</div>

			<h2 class="font-bold mb-2">Join with a Code</h2>
			<form onsubmit={joinGroup} class="flex flex-col gap-3">
				<input
					type="text"
					class="input input-bordered"
					bind:value={joinCode}
					placeholder="e.g. QUT2025"
					required
				/>
				<button type="submit" class="btn btn-outline" disabled={joining}>
					{joining ? 'Joining…' : 'Join Group'}
				</button>
			</form>
		</SectionCard>
	{:else}
		<SectionCard>
			<div class="flex items-center justify-between mb-3">
				<h1 class="text-xl font-bold">Group {group.id}</h1>
				<span class="badge {group.status === 'valid' ? 'badge-success' : 'badge-warning'} badge-lg">
					{group.status === 'valid' ? 'Valid' : 'Provisional'}
				</span>
			</div>

			{#if group.preference_code}
				<div class="flex items-center gap-2 mb-4">
					<span class="text-sm text-base-content/60">Invite code:</span>
					<span class="font-mono font-medium">{group.preference_code}</span>
					<button class="btn btn-ghost btn-xs" onclick={copyCode}>Copy</button>
				</div>
			{/if}

			{#if group.status === 'provisional'}
				<div role="alert" class="alert alert-warning mb-4">
					<div class="flex flex-col gap-2 text-sm">
						<p><strong>Provisional</strong>: no time slot is shared by all members yet.</p>
						{#if recommendedTimes.length > 0}
							<p>Recommended times shared by other members:</p>
							<ul class="list-disc list-inside">
								{#each recommendedTimes as slot}
									<li>{formatSlot(slot)}</li>
								{/each}
							</ul>
						{/if}
					</div>
				</div>
			{:else}
				<div role="alert" class="alert alert-success mb-4 text-sm">
					All members share: {group.common_time_slots.map(formatSlot).join(', ')}
				</div>
			{/if}

			{#if successMsg}<p class="text-success text-sm mb-2">{successMsg}</p>{/if}
			{#if error}<p class="text-error text-sm mb-2">{error}</p>{/if}

			<div class="divider"></div>
			<h2 class="font-bold mb-2">Members ({group.members.length}/5)</h2>
			<ul class="divide-y divide-base-200">
				{#each group.members as member}
					<li class="py-2 text-sm">{member.first_name} {member.last_name}</li>
				{/each}
			</ul>

			<div class="divider"></div>
			<button
				class="btn btn-outline btn-error btn-sm self-start"
				onclick={leaveGroup}
				disabled={leaving}
			>
				{leaving ? 'Leaving…' : 'Leave Group'}
			</button>
		</SectionCard>
	{/if}
</div>
```

- [ ] **Step 2: Type/compile check**

Run: `cd frontend && npm run check`
Expected: this file's prior errors are gone; remaining errors only in `/profile`.

- [ ] **Step 3: Manual check**

As a fresh unit member with no group: create a group (private), confirm the invite code and "Copy" button work, confirm status shows "Provisional". From a second test account in the same unit, join using that code; confirm both accounts now see updated member lists and matching/mismatched availability drives the Valid/Provisional badge correctly. Leave the group from one account and confirm it's removed.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/routes/group/+page.svelte
git commit -m "feat: rewrite group page for unit-scoped create/join/view"
```

---

### Task 20: Rewrite Profile page (`/profile`)

**Files:**
- Modify: `frontend/src/routes/profile/+page.svelte`

**Interfaces:**
- Consumes: `api.getMyUnitProfile`, `api.updateMyUnitProfile`, `api.getMyGroups` (`$lib/api`); `token`, `user`, `activeUnit` stores; `TimeGrid` (Task 7), `PageHeader` (Task 5), `SectionCard` (Task 6).

- [ ] **Step 1: Rewrite the page**

Replace the full contents of `frontend/src/routes/profile/+page.svelte` with:

```svelte
<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api, type GroupResponse, type UnitMeResponse } from '$lib/api';
	import { token, user, activeUnit } from '$lib/stores';
	import TimeGrid from '$lib/components/TimeGrid.svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import SectionCard from '$lib/components/SectionCard.svelte';

	let loading = $state(true);
	let saving = $state(false);
	let editMode = $state(false);
	let error = $state('');
	let successMsg = $state('');

	let unitProfile = $state<UnitMeResponse | null>(null);
	let myGroup = $state<GroupResponse | null>(null);

	let deliveryMode = $state('Online');
	let skills = $state('');
	let selectedSlots = $state(new Set<string>());

	onMount(async () => {
		if (!$token) {
			goto('/');
			return;
		}
		if (!$activeUnit) {
			goto('/onboarding/unit');
			return;
		}
		try {
			unitProfile = await api.getMyUnitProfile($activeUnit.id);
			syncForm(unitProfile);
			const groups = await api.getMyGroups();
			myGroup = groups.find((g) => g.unit_id === $activeUnit!.id) ?? null;
		} catch {
			error = 'Could not load your profile for this unit';
		} finally {
			loading = false;
		}
	});

	function syncForm(p: UnitMeResponse) {
		deliveryMode = p.delivery_mode ?? 'Online';
		skills = p.skills ?? '';
		selectedSlots = new Set(p.time_preferences);
	}

	function startEdit() {
		if (unitProfile) syncForm(unitProfile);
		successMsg = '';
		editMode = true;
	}

	function cancelEdit() {
		editMode = false;
		error = '';
	}

	function toggleSlot(slot: string) {
		const next = new Set(selectedSlots);
		if (next.has(slot)) next.delete(slot);
		else next.add(slot);
		selectedSlots = next;
	}

	function logout() {
		token.clear();
		user.set(null);
		activeUnit.clear();
		goto('/');
	}

	async function saveProfile(e: SubmitEvent) {
		e.preventDefault();
		if (!$activeUnit) return;
		error = '';
		saving = true;
		try {
			unitProfile = await api.updateMyUnitProfile($activeUnit.id, {
				delivery_mode: deliveryMode,
				skills: skills || undefined,
				time_preferences: [...selectedSlots]
			});
			editMode = false;
			successMsg = 'Profile updated.';
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Update failed';
		} finally {
			saving = false;
		}
	}
</script>

<PageHeader title={`Welcome, ${$user?.first_name ?? ''}!`} subtitle={`Student ID: ${$user?.id ?? ''}`}>
	{#snippet actions()}
		{#if !editMode}
			<button class="btn btn-outline btn-sm" onclick={startEdit}>Edit Profile</button>
		{/if}
		<button class="btn btn-ghost btn-sm" onclick={logout}>Logout</button>
	{/snippet}
</PageHeader>

<div class="max-w-3xl mx-auto px-4 py-8">
	{#if loading}
		<span class="loading loading-spinner"></span>
	{:else if editMode}
		<SectionCard title="Edit Profile">
			<form onsubmit={saveProfile} class="flex flex-col gap-3">
				<div class="flex flex-col gap-2">
					<span class="text-sm font-medium">Delivery Mode</span>
					<select class="select select-bordered" bind:value={deliveryMode}>
						<option value="Online">Online</option>
						<option value="In-person">In-person</option>
					</select>
				</div>
				<label class="flex flex-col gap-1">
					<span class="text-sm font-medium">Skills</span>
					<textarea class="textarea textarea-bordered" bind:value={skills} rows={3}></textarea>
				</label>
				<div class="flex flex-col gap-2">
					<span class="text-sm font-medium">Availability</span>
					<TimeGrid selected={selectedSlots} onToggle={toggleSlot} />
				</div>
				{#if error}<p class="text-error text-sm">{error}</p>{/if}
				<div class="flex gap-2 mt-1">
					<button type="submit" class="btn btn-primary btn-sm" disabled={saving}>
						{saving ? 'Saving…' : 'Save'}
					</button>
					<button type="button" class="btn btn-ghost btn-sm" onclick={cancelEdit}>Cancel</button>
				</div>
			</form>
		</SectionCard>
	{:else}
		<div class="grid gap-4 md:grid-cols-2">
			<SectionCard title="Your Schedule">
				<p class="text-sm text-base-content/60 mb-3">
					Times you've indicated you're available to meet.
				</p>
				<TimeGrid selected={new Set(unitProfile?.time_preferences ?? [])} readonly />
			</SectionCard>

			<SectionCard title="Profile Details">
				<dl class="flex flex-col gap-2 text-sm">
					<div>
						<dt class="text-base-content/60">Delivery Mode</dt>
						<dd>{unitProfile?.delivery_mode ?? '—'}</dd>
					</div>
					<div>
						<dt class="text-base-content/60">Skills</dt>
						<dd class="whitespace-pre-wrap">{unitProfile?.skills ?? '—'}</dd>
					</div>
				</dl>
			</SectionCard>

			<div class="md:col-span-2">
				<SectionCard title="Your Team">
					{#if successMsg}<p class="text-success text-sm mb-2">{successMsg}</p>{/if}
					{#if myGroup}
						<p class="text-sm">
							You're in Group {myGroup.id} with {myGroup.members.length} member{myGroup.members
								.length !== 1
								? 's'
								: ''}.
							<a href="/group" class="link">View your group →</a>
						</p>
					{:else}
						<p class="text-sm text-base-content/60">
							You haven't joined a group yet. <a href="/group" class="link">Create or join one →</a>
						</p>
					{/if}
				</SectionCard>
			</div>
		</div>
	{/if}
</div>
```

- [ ] **Step 2: Type/compile check**

Run: `cd frontend && npm run check`
Expected: **zero errors** — this was the last file with pre-existing errors from Task 3's model change.

- [ ] **Step 3: Manual check**

Visit `/profile`. Expected: schedule grid (read-only), profile details, "Your Team" summary, and header Edit Profile/Logout buttons all render. Click "Edit Profile", change availability/skills, save, confirm the read-only view updates.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/routes/profile/+page.svelte
git commit -m "feat: rewrite profile page with per-unit schedule and team summary"
```

---

### Task 21: Full end-to-end verification

**Files:** none (verification only).

- [ ] **Step 1: Fresh-account walkthrough**

With both servers running, in a private/incognito window: register a new account → create a new unit → complete unit setup (pick a few time slots) → land on `/home` → click through to `/explore` (confirm mock list, search, and degree filter work) → go to `/group` and create a private group → confirm the invite code shows and "Copy" works → go to `/profile` and confirm the schedule/details/team card all match what was entered → click "Logout" → log back in and confirm you land back on `/home` for the same unit (not re-prompted for onboarding).

- [ ] **Step 2: Second-unit walkthrough**

From the same account, use "Create a Unit" again from `/onboarding/unit` (navigate there directly) to join/create a second unit. Confirm the navbar's `UnitSwitcher` now lists both units, and switching updates `/home`, `/explore`, `/group`, and `/profile` to the newly selected unit's data.

- [ ] **Step 3: Multi-member group walkthrough**

Register a second account, join the same unit (using the first unit's code), then join the first account's group using its invite code. Confirm both accounts' `/group` pages show two members and the Valid/Provisional badge reflects whether their availabilities actually overlap.

- [ ] **Step 4: Final check**

Run: `cd frontend && npm run check`
Expected: zero errors, confirming the whole rewrite type-checks cleanly end to end.

- [ ] **Step 5: Commit**

If Steps 1-3 surfaced no code changes, there's nothing to commit — this task is verification-only. If any fix was needed, commit it separately with a message describing exactly what broke.
