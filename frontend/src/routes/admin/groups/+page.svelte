<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { token, activeUnit } from '$lib/stores';
	import { api, type GroupResponse } from '$lib/api';
	import PageHeader from '$lib/components/PageHeader.svelte';

	let groups = $state<GroupResponse[]>([]);
	let loadError = $state('');
	let removeError = $state('');
	let removingKey = $state<string | null>(null);
	let typeFilter = $state<'all' | 'public' | 'private'>('all');

	const filteredGroups = $derived(
		groups.filter((g) => typeFilter === 'all' || g.is_public === (typeFilter === 'public'))
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
		} catch {
			goto('/home');
			return;
		}
		try {
			groups = await api.getGroups($activeUnit.id);
		} catch (e: unknown) {
			loadError = e instanceof Error ? e.message : 'Could not load groups';
		}
	});

	async function removeMember(group: GroupResponse, userId: number) {
		if (!$activeUnit) return;
		removeError = '';
		const key = `${group.id}-${userId}`;
		removingKey = key;
		try {
			await api.removeGroupMember($activeUnit.id, group.id, userId);
			groups = groups.map((g) =>
				g.id === group.id ? { ...g, members: g.members.filter((m) => m.id !== userId) } : g
			);
		} catch (e: unknown) {
			removeError = e instanceof Error ? e.message : 'Could not remove member';
		} finally {
			removingKey = null;
		}
	}
</script>

<PageHeader
	title="Manage Groups"
	subtitle={`All groups in ${$activeUnit?.name ?? $activeUnit?.code ?? ''}`}
/>

<div class="max-w-3xl mx-auto px-4 py-8">
	<label class="flex flex-col gap-1 mb-4 max-w-xs">
		<span class="text-sm font-medium">Group type</span>
		<select class="select select-bordered select-sm" bind:value={typeFilter}>
			<option value="all">All</option>
			<option value="public">Public</option>
			<option value="private">Private</option>
		</select>
	</label>

	{#if loadError}<p class="text-error text-sm mb-2">{loadError}</p>{/if}
	{#if removeError}<p class="text-error text-sm mb-2">{removeError}</p>{/if}

	<div class="flex flex-col gap-4">
		{#each filteredGroups as group}
			<div class="card bg-base-100 shadow-sm rounded-2xl">
				<div class="card-body">
					<div class="flex items-center justify-between gap-2 mb-2">
						<p class="font-bold">Group {group.preference_code}</p>
						<span class="badge badge-ghost">{group.is_public ? 'Public' : 'Private'}</span>
					</div>
					{#if group.members.length === 0}
						<p class="text-sm text-base-content/60">No members (empty group).</p>
					{/if}
					<div class="flex flex-col gap-2">
						{#each group.members as member}
							<div class="flex items-center justify-between gap-2">
								<span>{member.first_name} {member.last_name}</span>
								<button
									type="button"
									class="btn btn-error btn-outline btn-xs"
									disabled={removingKey === `${group.id}-${member.id}`}
									onclick={() => removeMember(group, member.id)}
								>
									{removingKey === `${group.id}-${member.id}` ? 'Removing…' : 'Remove'}
								</button>
							</div>
						{/each}
					</div>
				</div>
			</div>
		{/each}
		{#if groups.length === 0}
			<p class="text-sm text-base-content/60">No groups in this unit yet.</p>
		{/if}
	</div>
</div>
