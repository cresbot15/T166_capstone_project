<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { token, activeUnit } from '$lib/stores';
	import { api, type UnitMemberResponse } from '$lib/api';
	import PageHeader from '$lib/components/PageHeader.svelte';

	let members = $state<UnitMemberResponse[]>([]);
	let isOwner = $state(false);
	let loadError = $state('');
	let roleUpdateError = $state('');
	let exportError = $state('');
	let exporting = $state(false);
	let saving = $state(false);
	let pendingRoles = $state<Record<number, 'administrator' | 'student'>>({});

	const hasPendingChanges = $derived(Object.keys(pendingRoles).length > 0);

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
			members = await api.getUnitMembers($activeUnit.id);
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

	<div class="flex flex-col gap-3">
		{#each members as member}
			<div class="card bg-base-100 shadow-sm rounded-2xl">
				<div class="card-body flex-row items-center justify-between gap-4">
					<a href={`/admin/students/${member.user_id}`} class="min-w-0 flex-1 hover:underline">
						<p class="font-bold">{member.first_name} {member.last_name}</p>
						<p class="text-sm text-base-content/60">{member.email}</p>
					</a>
					{#if isOwner && member.role !== 'owner'}
						<select
							class="select select-bordered select-sm"
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
