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

	async function changeRole(member: UnitMemberResponse, role: 'administrator' | 'student') {
		if (!$activeUnit) return;
		roleUpdateError = '';
		try {
			const updated = await api.setMemberRole($activeUnit.id, member.user_id, role);
			members = members.map((m) =>
				m.user_id === member.user_id ? { ...m, role: updated.role } : m
			);
		} catch (e: unknown) {
			roleUpdateError = e instanceof Error ? e.message : 'Could not update role';
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
					<div class="min-w-0 flex-1">
						<p class="font-bold">{member.first_name} {member.last_name}</p>
						<p class="text-sm text-base-content/60">{member.email}</p>
					</div>
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
		{/each}
		{#if members.length === 0}
			<p class="text-sm text-base-content/60">No members in this unit yet.</p>
		{/if}
	</div>
</div>
