<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { token, activeUnit } from '$lib/stores';
	import { api, type GroupResponse, type UnitMemberResponse } from '$lib/api';
	import { clickOutside } from '$lib/clickOutside';
	import { capitalize } from '$lib/format';
	import PageHeader from '$lib/components/PageHeader.svelte';

	let view = $state<'students' | 'groups'>('students');
	let search = $state('');

	let members = $state<UnitMemberResponse[]>([]);
	let membersError = $state('');

	let groups = $state<GroupResponse[]>([]);
	let myGroups = $state<GroupResponse[]>([]);
	let groupsError = $state('');
	let joiningGroupId = $state<number | null>(null);
	let myTimePreferences = $state<string[]>([]);

	let filtersOpen = $state(false);
	let statusFilter = $state<'all' | 'pending' | 'provisional'>('all');
	let openSlotsOnly = $state(false);
	let matchesMyAvailability = $state(false);

	let studentFiltersOpen = $state(false);
	let groupStatusDropdownOpen = $state(false);
	let showReady = $state(true);
	let showProvisional = $state(true);
	let showNoGroup = $state(true);
	const groupStatusFilterActive = $derived(!(showReady && showProvisional && showNoGroup));

	// Each active filter contributes one predicate; a future constraint (e.g. a
	// composition rule) just adds another entry here rather than reshaping this logic.
	const groupFilters = $derived(
		[
			statusFilter !== 'all' && ((g: GroupResponse) => g.status === statusFilter),
			openSlotsOnly &&
				((g: GroupResponse) => g.members.length < ($activeUnit?.max_group_size ?? Infinity)),
			matchesMyAvailability &&
				((g: GroupResponse) => g.common_time_slots.some((slot) => myTimePreferences.includes(slot)))
		].filter((f): f is (g: GroupResponse) => boolean => f !== false)
	);

	const filteredGroups = $derived(groups.filter((g) => groupFilters.every((f) => f(g))));
	const activeFilterCount = $derived(
		(statusFilter !== 'all' ? 1 : 0) +
			(openSlotsOnly ? 1 : 0) +
			(matchesMyAvailability ? 1 : 0)
	);
	const studentActiveFilterCount = $derived(groupStatusFilterActive ? 1 : 0);

	// Owners/admins see every group for the unit (public and private), so this
	// cross-reference is complete for anyone who can see the Students panel at all.
	const groupInfoByUserId = $derived.by(() => {
		const map = new Map<number, { id: number; status: GroupResponse['status'] }>();
		for (const g of groups) {
			for (const m of g.members) map.set(m.id, { id: g.id, status: g.status });
		}
		return map;
	});

	const filteredMembers = $derived.by(() => {
		const query = search.toLowerCase().trim();
		return members.filter((m) => {
			if (query) {
				const matchesQuery =
					`${m.first_name} ${m.last_name}`.toLowerCase().includes(query) ||
					(m.skills ?? '').toLowerCase().includes(query);
				if (!matchesQuery) return false;
			}
			if (m.role === 'student' && groupStatusFilterActive) {
				const status = groupInfoByUserId.get(m.user_id)?.status;
				if (status === 'pending' && !showReady) return false;
				if (status === 'provisional' && !showProvisional) return false;
				if (!status && !showNoGroup) return false;
			}
			return true;
		});
	});

	function membershipLabel(userId: number): { text: string; badgeClass: string } {
		const info = groupInfoByUserId.get(userId);
		if (!info) return { text: 'No group', badgeClass: 'badge-ghost' };
		if (info.status === 'pending') return { text: `Group ${info.id}`, badgeClass: 'badge-success' };
		return { text: `Group ${info.id} (provisional)`, badgeClass: 'badge-warning' };
	}

	const myGroupIdForUnit = $derived(
		myGroups.find((g) => g.unit_id === $activeUnit?.id)?.id ?? null
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
			myTimePreferences = profile.time_preferences;
		} catch {
			// no-op — myTimePreferences stays at its default
		}
		try {
			members = await api.getUnitMembers($activeUnit.id);
		} catch (e: unknown) {
			membersError = e instanceof Error ? e.message : 'Could not load members';
		}
		try {
			[groups, myGroups] = await Promise.all([api.getGroups($activeUnit.id), api.getMyGroups()]);
		} catch (e: unknown) {
			groupsError = e instanceof Error ? e.message : 'Could not load groups';
		}
	});

	async function joinGroup(group: GroupResponse) {
		if (!group.preference_code) return;
		groupsError = '';
		joiningGroupId = group.id;
		try {
			const result = await api.joinGroup(group.preference_code);
			if (!result.valid || !result.group) {
				groupsError = result.reason ?? 'Could not join group';
				return;
			}
			myGroups = [...myGroups, result.group];
			groups = groups.map((g) => (g.id === result.group!.id ? result.group! : g));
		} catch (e: unknown) {
			groupsError = e instanceof Error ? e.message : 'Could not join group';
		} finally {
			joiningGroupId = null;
		}
	}
</script>

<PageHeader
	title="Explore Students & Groups"
	subtitle={`Search for students and public groups in ${$activeUnit?.name ?? $activeUnit?.code ?? ''}`}
/>

<div class="max-w-5xl mx-auto px-4 py-8">
	<div role="tablist" class="tabs tabs-boxed mb-6 md:hidden">
		<button
			type="button"
			role="tab"
			class="tab {view === 'students' ? 'tab-active' : ''}"
			onclick={() => (view = 'students')}
		>
			Students
		</button>
		<button
			type="button"
			role="tab"
			class="tab {view === 'groups' ? 'tab-active' : ''}"
			onclick={() => (view = 'groups')}
		>
			Groups
		</button>
	</div>

	<div class="grid gap-8 md:grid-cols-2">
		<div class="{view === 'students' ? 'block' : 'hidden'} md:block">
			<h2 class="font-bold text-lg mb-3">Students</h2>

			<input
				type="text"
				class="input input-bordered w-full mb-4"
				placeholder="Search for students"
				bind:value={search}
			/>

			<button
				type="button"
				class="btn btn-outline btn-sm mb-3"
				onclick={() => (studentFiltersOpen = !studentFiltersOpen)}
			>
				Filters
				{#if studentActiveFilterCount > 0}<span class="badge badge-secondary badge-sm"
						>{studentActiveFilterCount}</span
					>{/if}
				<span class="text-xs">{studentFiltersOpen ? '▲' : '▼'}</span>
			</button>

			{#if studentFiltersOpen}
				<div class="card bg-base-100 shadow-sm rounded-2xl mb-4">
					<div class="card-body gap-3">
						<div class="flex flex-col gap-1">
							<span class="text-sm font-medium">Group status</span>
							<div
								class="dropdown"
								class:dropdown-open={groupStatusDropdownOpen}
								use:clickOutside={() => (groupStatusDropdownOpen = false)}
							>
								<button
									type="button"
									class="btn btn-outline btn-sm justify-between w-56"
									onclick={() => (groupStatusDropdownOpen = !groupStatusDropdownOpen)}
								>
									Group status
									{#if groupStatusFilterActive}<span class="badge badge-secondary badge-sm"
											>on</span
										>{/if}
									<span class="text-xs">▾</span>
								</button>
								<div
									class="dropdown-content menu bg-base-100 rounded-box shadow-sm z-10 w-56 p-3 gap-1"
								>
									<label class="flex items-center gap-2 py-1">
										<input
											type="checkbox"
											class="checkbox checkbox-sm checkbox-success border-2 border-secondary"
											bind:checked={showReady}
										/>
										<span class="text-sm">Ready</span>
									</label>
									<label class="flex items-center gap-2 py-1">
										<input
											type="checkbox"
											class="checkbox checkbox-sm checkbox-success border-2 border-secondary"
											bind:checked={showProvisional}
										/>
										<span class="text-sm">Provisional</span>
									</label>
									<label class="flex items-center gap-2 py-1">
										<input
											type="checkbox"
											class="checkbox checkbox-sm checkbox-success border-2 border-secondary"
											bind:checked={showNoGroup}
										/>
										<span class="text-sm">No group</span>
									</label>
								</div>
							</div>
						</div>
					</div>
				</div>
			{/if}

			{#if membersError}<p class="text-error text-sm mb-2">{membersError}</p>{/if}

			<div class="flex flex-col gap-3">
				{#each filteredMembers as member}
					{@const membership = membershipLabel(member.user_id)}
					<div class="card bg-base-100 shadow-sm rounded-2xl">
						<div class="card-body flex-row items-center justify-between gap-4">
							<div class="min-w-0 flex-1">
								<p class="font-bold">{member.first_name} {member.last_name}</p>
								<p class="text-sm text-base-content/60">
									Delivery: {capitalize(member.delivery_mode)}
								</p>
								<p class="text-sm text-base-content/60 break-words">
									Skills: {member.skills || '—'}
								</p>
								<span class="badge {membership.badgeClass} badge-sm mt-1">{membership.text}</span>
							</div>
							<div class="flex flex-col items-end gap-2 flex-shrink-0">
								{#if member.is_new_student}
									<span class="badge badge-accent badge-sm whitespace-nowrap">New student</span>
								{/if}
								<span class="badge badge-ghost capitalize">{member.role}</span>
							</div>
						</div>
					</div>
				{/each}
				{#if members.length === 0}
					<p class="text-sm text-base-content/60">No members in this unit yet.</p>
				{:else if filteredMembers.length === 0}
					<p class="text-sm text-base-content/60">No students match the selected filters.</p>
				{/if}
			</div>
		</div>

		<div class="{view === 'groups' ? 'block' : 'hidden'} md:block">
			<h2 class="font-bold text-lg mb-3">Public Groups</h2>

			<button
				type="button"
				class="btn btn-outline btn-sm mb-3"
				onclick={() => (filtersOpen = !filtersOpen)}
			>
				Filters
				{#if activeFilterCount > 0}<span class="badge badge-secondary badge-sm">{activeFilterCount}</span>{/if}
				<span class="text-xs">{filtersOpen ? '▲' : '▼'}</span>
			</button>

			{#if filtersOpen}
				<div class="card bg-base-100 shadow-sm rounded-2xl mb-4">
					<div class="card-body gap-3">
						<label class="flex flex-col gap-1">
							<span class="text-sm font-medium">Status</span>
							<select class="select select-bordered select-sm" bind:value={statusFilter}>
								<option value="all">All</option>
								<option value="pending">Ready</option>
								<option value="provisional">Provisional</option>
							</select>
						</label>
						<label class="flex items-center gap-2">
							<input type="checkbox" class="checkbox checkbox-sm" bind:checked={openSlotsOnly} />
							<span class="text-sm">Has open spots</span>
						</label>
						<label class="flex items-center gap-2">
							<input
								type="checkbox"
								class="checkbox checkbox-sm"
								bind:checked={matchesMyAvailability}
							/>
							<span class="text-sm">Matches my availability</span>
						</label>
					</div>
				</div>
			{/if}

			{#if groupsError}<p class="text-error text-sm mb-2">{groupsError}</p>{/if}
			<div class="flex flex-col gap-3">
				{#each filteredGroups as g}
					{@const isMine = g.id === myGroupIdForUnit}
					{@const blocked = myGroupIdForUnit !== null && !isMine}
					<div class="card bg-base-100 shadow-sm rounded-2xl">
						<div class="card-body flex-row items-center justify-between gap-4">
							<div class="min-w-0 flex-1">
								<p class="font-bold">Group {g.id}</p>
								<p class="text-sm text-base-content/60">
									{g.members.map((m) => m.first_name).join(', ') || 'No members yet'}
								</p>
							</div>
							<div class="flex items-center flex-wrap justify-end gap-2 flex-shrink-0">
								<span
									class="badge whitespace-nowrap {g.status === 'pending'
										? 'badge-success'
										: 'badge-warning'}"
								>
									{g.status === 'pending' ? 'Ready' : 'Provisional'}
								</span>
								{#if isMine}
									<span class="badge badge-ghost whitespace-nowrap">Your Group</span>
								{:else if blocked}
									<div
										class="tooltip"
										data-tip="You're already enrolled in a different group for this unit"
									>
										<button class="btn btn-primary btn-sm" disabled>Join</button>
									</div>
								{:else}
									<button
										class="btn btn-primary btn-sm"
										disabled={joiningGroupId === g.id}
										onclick={() => joinGroup(g)}
									>
										{joiningGroupId === g.id ? 'Joining…' : 'Join'}
									</button>
								{/if}
							</div>
						</div>
					</div>
				{/each}
				{#if groups.length === 0}
					<p class="text-sm text-base-content/60">No public groups yet.</p>
				{:else if filteredGroups.length === 0}
					<p class="text-sm text-base-content/60">No groups match the selected filters.</p>
				{/if}
			</div>
		</div>
	</div>
</div>
