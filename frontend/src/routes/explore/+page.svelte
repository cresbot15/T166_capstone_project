<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { token, activeUnit } from '$lib/stores';
	import { api, type GroupResponse } from '$lib/api';
	import { mockStudents, type MockStudent } from '$lib/mockStudents';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import StatusPill from '$lib/components/StatusPill.svelte';

	// Explore's student directory is mocked: no backend endpoint lists a unit's
	// students with degree/skills/group status (see design spec Non-goals). The
	// role-change call below is real (PATCH /units/{id}/members/{email}) but is
	// applied against these mock rows' emails, which won't correspond to real
	// unit members. The groups section below, by contrast, is entirely real —
	// GET /groups/{unit_id} and the join call both hit the live backend.

	let search = $state('');
	let degreeFilter = $state('All');
	let isOwner = $state(false);
	let roleUpdateError = $state('');

	let groups = $state<GroupResponse[]>([]);
	let myGroups = $state<GroupResponse[]>([]);
	let groupsError = $state('');
	let joiningGroupId = $state<number | null>(null);

	const degrees = $derived(['All', ...new Set(mockStudents.map((s) => s.degree))]);

	const filtered = $derived(
		mockStudents.filter((s) => {
			const matchesSearch = s.name.toLowerCase().includes(search.toLowerCase());
			const matchesDegree = degreeFilter === 'All' || s.degree === degreeFilter;
			return matchesSearch && matchesDegree;
		})
	);

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
		} catch {
			isOwner = false;
		}
		try {
			[groups, myGroups] = await Promise.all([api.getGroups($activeUnit.id), api.getMyGroups()]);
		} catch (e: unknown) {
			groupsError = e instanceof Error ? e.message : 'Could not load groups';
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

<div class="max-w-3xl mx-auto px-4 py-8">
	<h2 class="font-bold text-lg mb-3">Students</h2>
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

	<h2 class="font-bold text-lg mt-8 mb-3">Public Groups</h2>
	{#if groupsError}<p class="text-error text-sm mb-2">{groupsError}</p>{/if}
	<div class="flex flex-col gap-3">
		{#each groups as g}
			{@const isMine = g.id === myGroupIdForUnit}
			{@const blocked = myGroupIdForUnit !== null && !isMine}
			<div class="card bg-base-100 shadow-sm rounded-2xl">
				<div class="card-body flex-row items-center justify-between">
					<div>
						<p class="font-bold">Group {g.preference_code}</p>
						<p class="text-sm text-base-content/60">
							{g.members.map((m) => m.first_name).join(', ') || 'No members yet'}
						</p>
					</div>
					<div class="flex items-center gap-3">
						<span class="badge {g.status === 'valid' ? 'badge-success' : 'badge-warning'}">
							{g.status === 'valid' ? 'Valid' : 'Provisional'}
						</span>
						{#if isMine}
							<span class="badge badge-ghost">Your Group</span>
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
		{/if}
	</div>
</div>
