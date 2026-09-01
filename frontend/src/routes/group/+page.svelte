<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api, type GroupResponse, type UnitResponse } from '$lib/api';
	import { token, activeUnit } from '$lib/stores';
	import { formatSlot } from '$lib/timeslots';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import SectionCard from '$lib/components/SectionCard.svelte';

	let loading = $state(true);
	let group = $state<GroupResponse | null>(null);
	let recommendedTimes = $state<string[]>([]);
	let joinCode = $state('');
	let isPublic = $state(false);
	let error = $state('');
	let successMsg = $state('');
	let creating = $state(false);
	let joining = $state(false);
	let leaving = $state(false);

	const REQUIREMENT_LABELS: Record<string, (unit: UnitResponse) => string> = {
		min_group_size: (unit) => `Needs at least ${unit.min_group_size} members.`,
		common_time_slot: () => 'No time slot is shared by all members yet.',
		max_new_students: (unit) => `Too many new students for this group (unit max: ${unit.max_new_students}).`
	};

	onMount(async () => {
		if (!$token) {
			goto('/');
			return;
		}
		if (!$activeUnit) {
			goto('/onboarding/unit');
			return;
		}
		await loadGroup();
		loading = false;
	});

	async function loadGroup() {
		if (!$activeUnit) return;
		const groups = await api.getMyGroups();
		group = groups.find((g) => g.unit_id === $activeUnit!.id) ?? null;
		if (group && group.unmet_requirements.includes('common_time_slot')) {
			recommendedTimes = await api.getRecommendedTimes($activeUnit.id, group.id);
		} else {
			recommendedTimes = [];
		}
	}

	async function createGroup(e: SubmitEvent) {
		e.preventDefault();
		if (!$activeUnit) return;
		error = '';
		creating = true;
		try {
			group = await api.createGroup($activeUnit.id, isPublic);
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Failed to create group';
		} finally {
			creating = false;
		}
	}

	async function joinGroup(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		joining = true;
		try {
			const result = await api.joinGroup(joinCode);
			if (!result.valid || !result.group) {
				error = result.reason ?? 'Could not join group';
				return;
			}
			await loadGroup();
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Failed to join group';
		} finally {
			joining = false;
		}
	}

	async function leaveGroup() {
		if (!$activeUnit || !group) return;
		if (!confirm('Leave this group?')) return;
		error = '';
		leaving = true;
		try {
			await api.leaveGroup($activeUnit.id, group.id);
			group = null;
			recommendedTimes = [];
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Failed to leave group';
		} finally {
			leaving = false;
		}
	}

	function copyCode() {
		if (group?.preference_code) {
			navigator.clipboard.writeText(group.preference_code);
			successMsg = 'Invite code copied!';
		}
	}
</script>

<PageHeader title="My Group" subtitle={$activeUnit?.name ?? $activeUnit?.code} />

<div class="max-w-xl mx-auto px-4 py-8">
	{#if loading}
		<span class="loading loading-spinner"></span>
	{:else if !group}
		<SectionCard title="Create a Group">
			<form onsubmit={createGroup} class="flex flex-col gap-3 mb-6">
				<label class="flex flex-col gap-1">
					<span class="text-sm font-medium">Visibility</span>
					<select class="select select-bordered" bind:value={isPublic}>
						<option value={false}>Private — invite only</option>
						<option value={true}>Public — visible to the unit</option>
					</select>
				</label>
				{#if error}<p class="text-error text-sm">{error}</p>{/if}
				<button type="submit" class="btn btn-primary" disabled={creating}>
					{creating ? 'Creating…' : 'Create Group'}
				</button>
			</form>

			<div class="divider">or</div>

			<h2 class="font-bold mb-2">Join with a Code</h2>
			<form onsubmit={joinGroup} class="flex flex-col gap-3">
				<input
					type="text"
					class="input input-bordered"
					bind:value={joinCode}
					placeholder="e.g. QUT2025"
					required
				/>
				<button type="submit" class="btn btn-outline" disabled={joining}>
					{joining ? 'Joining…' : 'Join Group'}
				</button>
			</form>

			<div class="divider">or</div>

			<a href="/explore" class="btn btn-ghost btn-block">Browse Public Groups</a>
		</SectionCard>
	{:else}
		<SectionCard>
			<div class="flex items-center justify-between mb-3">
				<h1 class="text-xl font-bold">Group {group.id}</h1>
				<span class="badge {group.status === 'pending' ? 'badge-success' : 'badge-warning'} badge-lg">
					{group.status === 'pending' ? 'Ready' : 'Provisional'}
				</span>
			</div>

			{#if group.preference_code}
				<div class="flex items-center gap-2 mb-4">
					<span class="text-sm text-base-content/60">Invite code:</span>
					<span class="font-mono font-medium">{group.preference_code}</span>
					<button class="btn btn-ghost btn-xs" onclick={copyCode}>Copy</button>
				</div>
			{/if}

			{#if group.status === 'provisional'}
				<div role="alert" class="alert alert-warning mb-4">
					<div class="flex flex-col gap-2 text-sm">
						<p><strong>Provisional</strong>:</p>
						<ul class="list-disc list-inside">
							{#each group.unmet_requirements as req}
								<li>{$activeUnit ? REQUIREMENT_LABELS[req]?.($activeUnit) ?? req : req}</li>
							{/each}
						</ul>
						{#if recommendedTimes.length > 0}
							<p>Recommended times shared by other members:</p>
							<ul class="list-disc list-inside">
								{#each recommendedTimes as slot}
									<li>{formatSlot(slot)}</li>
								{/each}
							</ul>
						{/if}
					</div>
				</div>
			{:else}
				<div role="alert" class="alert alert-success mb-4 text-sm">
					All members share: {group.common_time_slots.map(formatSlot).join(', ')}
				</div>
			{/if}

			{#if successMsg}<p class="text-success text-sm mb-2">{successMsg}</p>{/if}
			{#if error}<p class="text-error text-sm mb-2">{error}</p>{/if}

			<div class="divider"></div>
			<h2 class="font-bold mb-2">Members ({group.members.length}/{$activeUnit?.max_group_size ?? '?'})</h2>
			<ul class="divide-y divide-base-200">
				{#each group.members as member}
					<li class="py-2 text-sm">{member.first_name} {member.last_name}</li>
				{/each}
			</ul>

			<div class="divider"></div>
			<button
				class="btn btn-outline btn-error btn-sm self-start"
				onclick={leaveGroup}
				disabled={leaving}
			>
				{leaving ? 'Leaving…' : 'Leave Group'}
			</button>
		</SectionCard>
	{/if}
</div>
