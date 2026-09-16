<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { token, activeUnit } from '$lib/stores';
	import { api, type UnitEventResponse, type UnitMemberResponse } from '$lib/api';
	import { eventLabel } from '$lib/auditLog';
	import { capitalize } from '$lib/format';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import TimeGrid from '$lib/components/TimeGrid.svelte';

	const userId = $derived(Number($page.params.userId));

	let member = $state<UnitMemberResponse | null>(null);
	let events = $state<UnitEventResponse[]>([]);
	let loadError = $state('');
	let notFound = $state(false);

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
			const [members, unitEvents] = await Promise.all([
				api.getUnitMembers($activeUnit.id),
				api.getUnitEvents($activeUnit.id, { userId })
			]);
			member = members.find((m) => m.user_id === userId) ?? null;
			notFound = member === null;
			events = unitEvents;
		} catch (e: unknown) {
			loadError = e instanceof Error ? e.message : 'Could not load student details';
		}
	});
</script>

<PageHeader
	title={member ? `${member.first_name} ${member.last_name}` : 'Student'}
	subtitle={`Student in ${$activeUnit?.name ?? $activeUnit?.code ?? ''}`}
/>

<div class="max-w-3xl mx-auto px-4 py-8 flex flex-col gap-6">
	{#if loadError}<p class="text-error text-sm">{loadError}</p>{/if}

	{#if notFound}
		<p class="text-sm text-base-content/60">
			This user is no longer a member of this unit. Their activity history is still shown below.
		</p>
	{/if}

	{#if member}
		<div class="card bg-base-100 shadow-sm rounded-2xl">
			<div class="card-body gap-2">
				<div class="flex items-center gap-2">
					<h2 class="text-lg font-bold">{member.first_name} {member.last_name}</h2>
					<span class="badge badge-ghost capitalize">{member.role}</span>
					{#if member.is_new_student}
						<span class="badge badge-accent">New student</span>
					{/if}
				</div>
				<p class="text-sm text-base-content/60">{member.email}</p>
				<div class="grid grid-cols-2 gap-x-4 gap-y-1 text-sm mt-2">
					<span class="text-base-content/60">Delivery mode</span>
					<span>{capitalize(member.delivery_mode)}</span>
					<span class="text-base-content/60">Skills</span>
					<span>{member.skills || '—'}</span>
				</div>
				<div class="mt-2">
					<span class="text-sm text-base-content/60">Time preferences</span>
					{#if member.time_preferences.length > 0}
						<TimeGrid
							slots={$activeUnit?.time_slots ?? []}
							selected={new Set(member.time_preferences)}
							readonly
						/>
					{:else}
						<p class="text-sm">—</p>
					{/if}
				</div>
			</div>
		</div>
	{/if}

	<div>
		<h3 class="font-bold mb-2">Activity</h3>
		<div class="flex flex-col gap-2">
			{#each events as event}
				<div class="card bg-base-100 shadow-sm rounded-2xl">
					<div class="card-body py-3 px-4 grid grid-cols-[1fr_auto] items-center gap-4">
						<p class="text-sm min-w-0">{eventLabel(event)}</p>
						<p class="text-xs text-base-content/60 whitespace-nowrap justify-self-end">
							{new Date(event.created_at).toLocaleString()}
						</p>
					</div>
				</div>
			{/each}
			{#if events.length === 0}
				<p class="text-sm text-base-content/60">No activity yet.</p>
			{/if}
		</div>
	</div>
</div>
