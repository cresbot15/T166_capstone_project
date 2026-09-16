<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { token, activeUnit } from '$lib/stores';
	import { api, type UnitEventResponse, type GroupResponse, type UnitMemberResponse } from '$lib/api';
	import { eventLabel } from '$lib/auditLog';
	import { formatSlot } from '$lib/timeslots';
	import { REQUIREMENT_LABELS } from '$lib/groupRequirements';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import TimeGrid from '$lib/components/TimeGrid.svelte';

	const groupId = $derived(Number($page.params.groupId));

	let group = $state<GroupResponse | null>(null);
	let events = $state<UnitEventResponse[]>([]);
	let unitMembers = $state<UnitMemberResponse[]>([]);
	let loadError = $state('');
	let notFound = $state(false);

	// If the group already has full agreement, use that directly. Otherwise
	// find the slot(s) that the most current members agree on, and who'd need
	// to change their availability to make that unanimous.
	const bestAvailability = $derived.by(() => {
		const empty = { slots: new Set<string>(), unavailableBySlot: new Map<string, string[]>(), fullyCommon: false };
		if (!group || !$activeUnit) return empty;

		if (group.common_time_slots.length > 0) {
			return { slots: new Set(group.common_time_slots), unavailableBySlot: new Map(), fullyCommon: true };
		}
		if (group.members.length === 0) return empty;

		const prefsByUserId = new Map(unitMembers.map((m) => [m.user_id, new Set(m.time_preferences)]));
		const countBySlot = new Map<string, number>();
		let maxCount = 0;
		for (const slot of $activeUnit.time_slots) {
			const count = group.members.filter((m) => prefsByUserId.get(m.id)?.has(slot)).length;
			countBySlot.set(slot, count);
			if (count > maxCount) maxCount = count;
		}
		if (maxCount === 0) return empty;

		const slots = new Set<string>();
		const unavailableBySlot = new Map<string, string[]>();
		for (const slot of $activeUnit.time_slots) {
			if (countBySlot.get(slot) !== maxCount) continue;
			slots.add(slot);
			unavailableBySlot.set(
				slot,
				group.members.filter((m) => !prefsByUserId.get(m.id)?.has(slot)).map((m) => m.first_name)
			);
		}
		return { slots, unavailableBySlot, fullyCommon: false };
	});

	function availabilityTitle(slot: string): string | undefined {
		if (!bestAvailability.slots.has(slot)) return undefined;
		const base = formatSlot(slot);
		if (bestAvailability.fullyCommon) return `${base} — everyone is available`;
		const unavailable = bestAvailability.unavailableBySlot.get(slot) ?? [];
		if (unavailable.length === 0) return `${base} — everyone is available`;
		return `${base} — not available: ${unavailable.join(', ')}`;
	}

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
			const [groups, groupEvents, members] = await Promise.all([
				api.getGroups($activeUnit.id),
				api.getUnitEvents($activeUnit.id, { groupId }),
				api.getUnitMembers($activeUnit.id)
			]);
			group = groups.find((g) => g.id === groupId) ?? null;
			notFound = group === null;
			events = groupEvents;
			unitMembers = members;
		} catch (e: unknown) {
			loadError = e instanceof Error ? e.message : 'Could not load group details';
		}
	});
</script>

<PageHeader
	title={group ? `Group ${group.id}` : 'Group'}
	subtitle={`Group in ${$activeUnit?.name ?? $activeUnit?.code ?? ''}`}
/>

<div class="max-w-3xl mx-auto px-4 py-8 flex flex-col gap-6">
	{#if loadError}<p class="text-error text-sm">{loadError}</p>{/if}

	{#if notFound}
		<p class="text-sm text-base-content/60">
			This group no longer exists. Its activity history is still shown below.
		</p>
	{/if}

	{#if group}
		<div class="card bg-base-100 shadow-sm rounded-2xl">
			<div class="card-body gap-2">
				<div class="flex items-center gap-2">
					<h2 class="text-lg font-bold">Group {group.id}</h2>
					<span class="badge badge-ghost">{group.is_public ? 'Public' : 'Private'}</span>
					<span class="badge {group.status === 'pending' ? 'badge-success' : 'badge-warning'}">
						{group.status === 'pending' ? 'Ready' : 'Provisional'}
					</span>
				</div>
				<p class="text-xs text-base-content/60 font-mono">{group.preference_code}</p>

				{#if group.status === 'provisional'}
					<ul class="list-disc list-inside text-sm text-base-content/70">
						{#each group.unmet_requirements as req}
							<li>{$activeUnit ? REQUIREMENT_LABELS[req]?.($activeUnit) ?? req : req}</li>
						{/each}
					</ul>
				{/if}

				<div class="mt-2">
					<span class="text-sm text-base-content/60">Members</span>
					{#if group.members.length > 0}
						<ul class="list-disc list-inside text-sm">
							{#each group.members as member}
								<li>
									<a href={`/admin/students/${member.id}`} class="hover:underline">
										{member.first_name} {member.last_name}
									</a>
								</li>
							{/each}
						</ul>
					{:else}
						<p class="text-sm">No members (empty group).</p>
					{/if}
				</div>
			</div>
		</div>

		{#if group.members.length > 0}
			<div class="card bg-base-100 shadow-sm rounded-2xl">
				<div class="card-body">
					<h3 class="font-bold mb-1">Common Availability</h3>
					{#if bestAvailability.slots.size === 0}
						<p class="text-sm text-base-content/60">
							No overlapping availability found among current members.
						</p>
					{:else if bestAvailability.fullyCommon}
						<p class="text-sm text-base-content/60 mb-3">Times that work for every member.</p>
						<TimeGrid
							slots={$activeUnit?.time_slots ?? []}
							selected={bestAvailability.slots}
							readonly
							titleFor={availabilityTitle}
						/>
					{:else}
						<p class="text-sm text-base-content/60 mb-3">
							No single time works for everyone yet — the highlighted times work for the most
							members. Hover a highlighted time to see who's unavailable.
						</p>
						<TimeGrid
							slots={$activeUnit?.time_slots ?? []}
							selected={bestAvailability.slots}
							readonly
							titleFor={availabilityTitle}
						/>
					{/if}
				</div>
			</div>
		{/if}
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
