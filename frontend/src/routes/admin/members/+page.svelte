<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { token, activeUnit } from '$lib/stores';
	import { api, type GroupResponse, type UnitMemberResponse } from '$lib/api';
	import { clickOutside } from '$lib/clickOutside';
	import PageHeader from '$lib/components/PageHeader.svelte';

	let members = $state<UnitMemberResponse[]>([]);
	let groups = $state<GroupResponse[]>([]);
	let isOwner = $state(false);
	let loadError = $state('');
	let roleUpdateError = $state('');
	let exportError = $state('');
	let exporting = $state(false);
	let saving = $state(false);
	let pendingRoles = $state<Record<number, 'administrator' | 'student'>>({});

	const hasPendingChanges = $derived(Object.keys(pendingRoles).length > 0);

	let filtersOpen = $state(false);
	let groupStatusDropdownOpen = $state(false);
	let roleFilter = $state<'all' | 'student' | 'administrator' | 'owner'>('all');
	let showReady = $state(true);
	let showProvisional = $state(true);
	let showNoGroup = $state(true);
	const groupStatusFilterActive = $derived(!(showReady && showProvisional && showNoGroup));
	const activeFilterCount = $derived(
		(roleFilter !== 'all' ? 1 : 0) + (groupStatusFilterActive ? 1 : 0)
	);

	// Staff see every group in the unit (public and private), so this is a
	// complete cross-reference on this page.
	const groupInfoByUserId = $derived.by(() => {
		const map = new Map<number, { id: number; status: GroupResponse['status'] }>();
		for (const g of groups) {
			for (const m of g.members) map.set(m.id, { id: g.id, status: g.status });
		}
		return map;
	});

	function groupBadge(userId: number): { text: string; badgeClass: string } {
		const info = groupInfoByUserId.get(userId);
		if (!info) return { text: 'No group', badgeClass: 'badge-ghost' };
		if (info.status === 'pending') return { text: `Group ${info.id}`, badgeClass: 'badge-success' };
		return { text: `Group ${info.id} (provisional)`, badgeClass: 'badge-warning' };
	}

	const filteredMembers = $derived(
		members.filter((m) => {
			if (roleFilter !== 'all' && m.role !== roleFilter) return false;
			if (m.role === 'student' && groupStatusFilterActive) {
				const status = groupInfoByUserId.get(m.user_id)?.status;
				if (status === 'pending' && !showReady) return false;
				if (status === 'provisional' && !showProvisional) return false;
				if (!status && !showNoGroup) return false;
			}
			return true;
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
			if (profile.role !== 'owner' && profile.role !== 'administrator') {
				goto('/home');
				return;
			}
			isOwner = profile.role === 'owner';
		} catch {
			goto('/home');
			return;
		}
		try {
			[members, groups] = await Promise.all([
				api.getUnitMembers($activeUnit.id),
				api.getGroups($activeUnit.id)
			]);
		} catch (e: unknown) {
			loadError = e instanceof Error ? e.message : 'Could not load members';
		}
	});

	function setPendingRole(member: UnitMemberResponse, role: 'administrator' | 'student') {
		if (role === member.role) {
			const { [member.user_id]: _, ...rest } = pendingRoles;
			pendingRoles = rest;
		} else {
			pendingRoles = { ...pendingRoles, [member.user_id]: role };
		}
	}

	function discardChanges() {
		pendingRoles = {};
		roleUpdateError = '';
	}

	async function saveChanges() {
		if (!$activeUnit) return;
		roleUpdateError = '';
		saving = true;
		try {
			const updates = await Promise.all(
				Object.entries(pendingRoles).map(([userId, role]) =>
					api.setMemberRole($activeUnit!.id, Number(userId), role)
				)
			);
			const updatedById = new Map(updates.map((u) => [u.user_id, u.role]));
			members = members.map((m) =>
				updatedById.has(m.user_id) ? { ...m, role: updatedById.get(m.user_id)! } : m
			);
			pendingRoles = {};
		} catch (e: unknown) {
			roleUpdateError = e instanceof Error ? e.message : 'Could not update roles';
		} finally {
			saving = false;
		}
	}

	async function exportCsv() {
		if (!$activeUnit) return;
		exportError = '';
		exporting = true;
		try {
			await api.exportUnitStudents($activeUnit.id);
		} catch (e: unknown) {
			exportError = e instanceof Error ? e.message : 'Could not export students';
		} finally {
			exporting = false;
		}
	}
</script>

<PageHeader
	title="Manage Members"
	subtitle={`Members of ${$activeUnit?.name ?? $activeUnit?.code ?? ''}`}
>
	{#snippet actions()}
		<button type="button" class="btn btn-secondary btn-sm" disabled={exporting} onclick={exportCsv}>
			{exporting ? 'Exporting…' : 'Export CSV'}
		</button>
	{/snippet}
</PageHeader>

<div class="max-w-3xl mx-auto px-4 py-8">
	{#if loadError}<p class="text-error text-sm mb-2">{loadError}</p>{/if}
	{#if roleUpdateError}<p class="text-error text-sm mb-2">{roleUpdateError}</p>{/if}
	{#if exportError}<p class="text-error text-sm mb-2">{exportError}</p>{/if}

	<button
		type="button"
		class="btn btn-outline btn-sm mb-3"
		onclick={() => (filtersOpen = !filtersOpen)}
	>
		Filters
		{#if activeFilterCount > 0}<span class="badge badge-secondary badge-sm"
				>{activeFilterCount}</span
			>{/if}
		<span class="text-xs">{filtersOpen ? '▲' : '▼'}</span>
	</button>

	{#if filtersOpen}
		<div class="card bg-base-100 shadow-sm rounded-2xl mb-4">
			<div class="card-body gap-3">
				<label class="flex flex-col gap-1">
					<span class="text-sm font-medium">Role</span>
					<select class="select select-bordered select-sm" bind:value={roleFilter}>
						<option value="all">All</option>
						<option value="student">Student</option>
						<option value="administrator">Administrator</option>
						<option value="owner">Owner</option>
					</select>
				</label>
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
							{#if groupStatusFilterActive}<span class="badge badge-secondary badge-sm">on</span
								>{/if}
							<span class="text-xs">▾</span>
						</button>
						<div
							class="dropdown-content menu bg-base-100 rounded-box shadow-sm z-10 w-56 p-3 gap-1"
						>
							<label class="flex items-center gap-2 py-1">
								<input type="checkbox" class="checkbox checkbox-sm checkbox-success border-2 border-secondary" bind:checked={showReady} />
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
								<input type="checkbox" class="checkbox checkbox-sm checkbox-success border-2 border-secondary" bind:checked={showNoGroup} />
								<span class="text-sm">No group</span>
							</label>
						</div>
					</div>
				</div>
			</div>
		</div>
	{/if}

	<div class="flex flex-col gap-3">
		{#each filteredMembers as member}
			{@const membership = groupBadge(member.user_id)}
			<div class="card bg-base-100 shadow-sm rounded-2xl">
				<div class="card-body flex-row items-start justify-between gap-4 flex-wrap">
					<a href={`/admin/students/${member.user_id}`} class="min-w-0 flex-1 hover:underline">
						<p class="font-bold">{member.first_name} {member.last_name}</p>
						<p class="text-sm text-base-content/60">{member.email}</p>
						{#if member.role === 'student'}
							<span class="badge {membership.badgeClass} badge-sm mt-1">{membership.text}</span>
						{/if}
					</a>
					{#if isOwner && member.role !== 'owner'}
						<select
							class="select select-bordered select-sm flex-shrink-0"
							value={pendingRoles[member.user_id] ?? member.role}
							onchange={(e) =>
								setPendingRole(member, e.currentTarget.value as 'administrator' | 'student')}
						>
							<option value="student">Student</option>
							<option value="administrator">Administrator</option>
						</select>
					{:else}
						<span class="badge badge-ghost capitalize">{member.role}</span>
					{/if}
				</div>
			</div>
		{/each}
		{#if members.length === 0}
			<p class="text-sm text-base-content/60">No members in this unit yet.</p>
		{:else if filteredMembers.length === 0}
			<p class="text-sm text-base-content/60">No members match the selected filters.</p>
		{/if}
	</div>

	{#if hasPendingChanges}
		<div class="sticky bottom-4 mt-6 flex justify-end gap-2">
			<button type="button" class="btn btn-ghost btn-sm" disabled={saving} onclick={discardChanges}>
				Discard changes
			</button>
			<button type="button" class="btn btn-primary btn-sm" disabled={saving} onclick={saveChanges}>
				{saving ? 'Saving…' : 'Save changes'}
			</button>
		</div>
	{/if}
</div>
