<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { token, activeUnit } from '$lib/stores';
	import { api, type GroupResponse, type UnitMemberResponse } from '$lib/api';
	import PageHeader from '$lib/components/PageHeader.svelte';

	let view = $state<'students' | 'groups'>('students');
	let search = $state('');
	let isOwner = $state(false);
	let isStaff = $state(false);
	let roleUpdateError = $state('');

	let members = $state<UnitMemberResponse[]>([]);
	let membersError = $state('');

	let groups = $state<GroupResponse[]>([]);
	let myGroups = $state<GroupResponse[]>([]);
	let groupsError = $state('');
	let joiningGroupId = $state<number | null>(null);
	let myTimePreferences = $state<string[]>([]);

	let filtersOpen = $state(false);
	let statusFilter = $state<'all' | 'pending' | 'provisional'>('all');
	let typeFilter = $state<'all' | 'public' | 'private'>('all');
	let openSlotsOnly = $state(false);
	let matchesMyAvailability = $state(false);

	// Each active filter contributes one predicate; a future constraint (e.g. a
	// composition rule) just adds another entry here rather than reshaping this logic.
	const groupFilters = $derived(
		[
			statusFilter !== 'all' && ((g: GroupResponse) => g.status === statusFilter),
			typeFilter !== 'all' && ((g: GroupResponse) => g.is_public === (typeFilter === 'public')),
			openSlotsOnly &&
				((g: GroupResponse) => g.members.length < ($activeUnit?.max_group_size ?? Infinity)),
			matchesMyAvailability &&
				((g: GroupResponse) => g.common_time_slots.some((slot) => myTimePreferences.includes(slot)))
		].filter((f): f is (g: GroupResponse) => boolean => f !== false)
	);

	const filteredGroups = $derived(groups.filter((g) => groupFilters.every((f) => f(g))));
	const activeFilterCount = $derived(
		(statusFilter !== 'all' ? 1 : 0) +
			(typeFilter !== 'all' ? 1 : 0) +
			(openSlotsOnly ? 1 : 0) +
			(matchesMyAvailability ? 1 : 0)
	);

	const filteredMembers = $derived(
		members.filter((m) =>
			`${m.first_name} ${m.last_name}`.toLowerCase().includes(search.toLowerCase())
		)
	);

	// Owners/admins see every group for the unit (public and private), so this
	// cross-reference is complete for anyone who can see the Students panel at all.
	const groupStatusByUserId = $derived.by(() => {
		const map = new Map<number, GroupResponse['status']>();
		for (const g of groups) {
			for (const m of g.members) map.set(m.id, g.status);
		}
		return map;
	});

	function membershipLabel(userId: number): { text: string; badgeClass: string } {
		const status = groupStatusByUserId.get(userId);
		if (!status) return { text: 'Not in a group', badgeClass: 'badge-ghost' };
		if (status === 'pending') return { text: 'In a group', badgeClass: 'badge-success' };
		return { text: 'In a provisional group', badgeClass: 'badge-warning' };
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
			isOwner = profile.role === 'owner';
			isStaff = profile.role === 'owner' || profile.role === 'administrator';
			myTimePreferences = profile.time_preferences;
		} catch {
			isOwner = false;
			isStaff = false;
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

	async function changeRole(member: UnitMemberResponse, role: 'administrator' | 'student') {
		if (!$activeUnit) return;
		roleUpdateError = '';
		try {
			const updated = await api.setMemberRole($activeUnit.id, member.user_id, role);
			members = members.map((m) => (m.user_id === member.user_id ? { ...m, role: updated.role } : m));
		} catch (e: unknown) {
			roleUpdateError = e instanceof Error ? e.message : 'Could not update role';
		}
	}

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

			{#if roleUpdateError}<p class="text-error text-sm mb-2">{roleUpdateError}</p>{/if}
			{#if membersError}<p class="text-error text-sm mb-2">{membersError}</p>{/if}

			<div class="flex flex-col gap-3">
				{#each filteredMembers as member}
					{@const membership = membershipLabel(member.user_id)}
					<div class="card bg-base-100 shadow-sm rounded-2xl">
						<div class="card-body flex-row items-center justify-between gap-4">
							<div class="min-w-0 flex-1">
								<p class="font-bold">{member.first_name} {member.last_name}</p>
								<p class="text-sm text-base-content/60">
									Delivery: {member.delivery_mode ?? '—'}
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
								{#if isOwner && member.role !== 'owner'}
									<select
										class="select select-bordered select-sm"
										value={member.role}
										onchange={(e) =>
											changeRole(member, e.currentTarget.value as 'administrator' | 'student')}
									>
										<option value="student">Student</option>
										<option value="administrator">Administrator</option>
									</select>
								{:else}
									<span class="badge badge-ghost capitalize">{member.role}</span>
								{/if}
							</div>
						</div>
					</div>
				{/each}
				{#if members.length === 0}
					<p class="text-sm text-base-content/60">No members in this unit yet.</p>
				{/if}
			</div>
		</div>

		<div class="{view === 'groups' ? 'block' : 'hidden'} md:block">
			<h2 class="font-bold text-lg mb-3">{isStaff ? 'Groups' : 'Public Groups'}</h2>

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
						{#if isStaff}
							<label class="flex flex-col gap-1">
								<span class="text-sm font-medium">Group type</span>
								<select class="select select-bordered select-sm" bind:value={typeFilter}>
									<option value="all">All</option>
									<option value="public">Public</option>
									<option value="private">Private</option>
								</select>
							</label>
						{/if}
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
								<p class="font-bold">Group {g.preference_code}</p>
								<p class="text-sm text-base-content/60">
									{g.members.map((m) => m.first_name).join(', ') || 'No members yet'}
								</p>
							</div>
							<div class="flex items-center flex-wrap justify-end gap-2 flex-shrink-0">
								{#if isStaff}
									<span class="badge badge-ghost whitespace-nowrap"
										>{g.is_public ? 'Public' : 'Private'}</span
									>
								{/if}
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
