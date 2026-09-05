<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { token, activeUnit } from '$lib/stores';
	import { api, type UnitEventResponse, type GroupResponse, type UnitMemberResponse } from '$lib/api';
	import PageHeader from '$lib/components/PageHeader.svelte';

	let events = $state<UnitEventResponse[]>([]);
	let groups = $state<GroupResponse[]>([]);
	let members = $state<UnitMemberResponse[]>([]);
	let loadError = $state('');
	let groupFilter = $state<number | null>(null);
	let userFilter = $state<number | null>(null);

	async function loadEvents() {
		if (!$activeUnit) return;
		loadError = '';
		try {
			if (groupFilter !== null) {
				events = await api.getUnitEvents($activeUnit.id, { groupId: groupFilter });
			} else if (userFilter !== null) {
				events = await api.getUnitEvents($activeUnit.id, { userId: userFilter });
			} else {
				events = await api.getUnitEvents($activeUnit.id);
			}
		} catch (e: unknown) {
			loadError = e instanceof Error ? e.message : 'Could not load audit log';
		}
	}

	function selectGroup(value: string) {
		groupFilter = value === '' ? null : Number(value);
		if (groupFilter !== null) userFilter = null;
		loadEvents();
	}

	function selectUser(value: string) {
		userFilter = value === '' ? null : Number(value);
		if (userFilter !== null) groupFilter = null;
		loadEvents();
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
			[groups, members] = await Promise.all([
				api.getGroups($activeUnit.id),
				api.getUnitMembers($activeUnit.id)
			]);
		} catch {
			groups = [];
			members = [];
		}
		await loadEvents();
	});

	function eventLabel(event: UnitEventResponse): string {
		const actor = event.actor_name ?? 'Someone';
		const subject = event.subject_name;
		switch (event.event_type) {
			case 'unit.member_joined':
				return `${actor} joined the unit`;
			case 'unit.member_left':
				return `${actor} left the unit`;
			case 'unit.role_changed':
				return `${actor} changed ${subject ?? 'a member'}'s role`;
			case 'group.created':
				return `${actor} created a group`;
			case 'group.deleted':
				return `${actor} deleted a group`;
			case 'group.member_joined':
				return `${actor} joined a group`;
			case 'group.member_left':
				return `${actor} left a group`;
			case 'group.member_removed':
				return `${actor} removed ${subject ?? 'a member'} from a group`;
			case 'group.status_changed':
				return `A group's status changed`;
			default:
				return event.event_type;
		}
	}
</script>

<PageHeader
	title="Audit Log"
	subtitle={`Recent activity in ${$activeUnit?.name ?? $activeUnit?.code ?? ''}`}
/>

<div class="max-w-3xl mx-auto px-4 py-8">
	<div class="flex flex-wrap gap-4 mb-4">
		<label class="flex flex-col gap-1 max-w-xs">
			<span class="text-sm font-medium">Group</span>
			<select
				class="select select-bordered select-sm"
				value={groupFilter ?? ''}
				onchange={(e) => selectGroup(e.currentTarget.value)}
			>
				<option value="">All groups</option>
				{#each groups as group}
					<option value={group.id}>Group {group.preference_code}</option>
				{/each}
			</select>
		</label>
		<label class="flex flex-col gap-1 max-w-xs">
			<span class="text-sm font-medium">User</span>
			<select
				class="select select-bordered select-sm"
				value={userFilter ?? ''}
				onchange={(e) => selectUser(e.currentTarget.value)}
			>
				<option value="">All users</option>
				{#each members as member}
					<option value={member.user_id}>{member.first_name} {member.last_name}</option>
				{/each}
			</select>
		</label>
	</div>

	{#if loadError}<p class="text-error text-sm mb-2">{loadError}</p>{/if}

	<div class="flex flex-col gap-2">
		{#each events as event}
			<div class="card bg-base-100 shadow-sm rounded-2xl">
				<div class="card-body py-3 px-4 flex-row items-center justify-between gap-4">
					<p class="text-sm min-w-0 flex-1">{eventLabel(event)}</p>
					<p class="text-xs text-base-content/60 whitespace-nowrap flex-shrink-0">
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
