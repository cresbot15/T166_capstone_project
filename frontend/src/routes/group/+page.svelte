<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api, type GroupResponse } from '$lib/api';
	import { token, user } from '$lib/stores';
	import { formatSlot } from '$lib/timeslots';

	let loading = $state(true);
	let group = $state<GroupResponse | null>(null);
	let recommendedTimes = $state<string[]>([]);
	let joinCode = $state('');
	let error = $state('');
	let successMsg = $state('');
	let joining = $state(false);
	let leaving = $state(false);
	let applying = $state(false);

	onMount(async () => {
		if (!$token) {
			goto('/');
			return;
		}
		await loadGroup();
		loading = false;
	});

	async function loadGroup() {
		try {
			group = await api.getMyGroup();
			if (group.status === 'provisional') {
				recommendedTimes = await api.getRecommendedTimes();
			} else {
				recommendedTimes = [];
			}
		} catch {
			group = null;
		}
	}

	async function joinGroup(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		successMsg = '';
		joining = true;
		try {
			const result = await api.joinGroup(joinCode);
			if (!result.valid) {
				error = result.reason ?? 'Could not join group';
				return;
			}
			group = result.group;
			if (group.status === 'provisional') {
				recommendedTimes = await api.getRecommendedTimes();
			}
			const me = await api.getMe();
			user.set(me);
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Failed to join group';
		} finally {
			joining = false;
		}
	}

	async function applyRecommendedTimes() {
		error = '';
		successMsg = '';
		applying = true;
		try {
			const currentPrefs = $user?.time_preferences ?? [];
			const merged = [...new Set([...currentPrefs, ...recommendedTimes])];
			const updated = await api.updateMe({ time_preferences: merged });
			user.set(updated);
			await loadGroup();
			if (group?.status === 'valid') {
				successMsg = 'Group is now valid: all members share a common time slot!';
			}
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Failed to update preferences';
		} finally {
			applying = false;
		}
	}

	async function leaveGroup() {
		if (!confirm('Leave this group?')) return;
		error = '';
		leaving = true;
		try {
			await api.leaveGroup();
			group = null;
			recommendedTimes = [];
			const me = await api.getMe();
			user.set(me);
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Failed to leave group';
		} finally {
			leaving = false;
		}
	}
</script>

{#if loading}
	<div class="max-w-xl mx-auto py-10 px-4">
		<span class="loading loading-spinner"></span>
	</div>
{:else}
	<div class="max-w-xl mx-auto py-8 px-4">
		{#if !group}
			<div class="card bg-base-100 border border-base-300 shadow-sm">
				<div class="card-body">
					<h1 class="text-xl font-semibold mb-1">Join a Group</h1>
					<p class="text-sm text-base-content/60 mb-4">
						Enter a preference code to join an existing group.
					</p>
					<form onsubmit={joinGroup} class="flex flex-col gap-3">
						<label class="flex flex-col gap-1">
							<span class="text-sm font-medium">Preference Code</span>
							<input
								type="text"
								class="input input-bordered"
								bind:value={joinCode}
								placeholder="e.g. QUT2025"
								required
							/>
						</label>
						{#if error}
							<p class="text-error text-sm">{error}</p>
						{/if}
						<button type="submit" class="btn btn-primary" disabled={joining}>
							{joining ? 'Joining…' : 'Join Group'}
						</button>
					</form>
				</div>
			</div>
		{:else}
			<div class="card bg-base-100 border border-base-300 shadow-sm">
				<div class="card-body">
					<div class="flex items-center justify-between mb-3">
						<h1 class="text-xl font-semibold">My Group</h1>
						<span class="badge {group.status === 'valid' ? 'badge-success' : 'badge-warning'} badge-lg">
							{group.status}
						</span>
					</div>

					{#if group.preference_code}
						<p class="text-sm text-base-content/60 mb-3">
							Code: <span class="font-medium text-base-content">{group.preference_code}</span>
						</p>
					{/if}

					{#if group.status === 'provisional'}
						<div role="alert" class="alert alert-warning mb-4">
							<div class="flex flex-col gap-2 text-sm">
								<p>
									<strong>Provisional</strong>: 
								</p>
								<p>No time slot is shared by all members.</p>
								{#if recommendedTimes.length > 0}
									<p>
										Recommended times (shared by the other {group.members.length - 1} member{group.members.length - 1 !== 1 ? 's' : ''}):
									</p>
									<ul class="list-disc list-inside">
										{#each recommendedTimes as slot}
											<li>{formatSlot(slot)}</li>
										{/each}
									</ul>
									<button
										class="btn btn-sm btn-primary mt-1 self-start"
										onclick={applyRecommendedTimes}
										disabled={applying}
									>
										{applying ? 'Applying…' : 'Add recommended times to my availability'}
									</button>
								{:else}
									<p>No common times exist among the other members yet.</p>
								{/if}
							</div>
						</div>
					{:else}
						<div role="alert" class="alert alert-success mb-4 text-sm">
							<span>
								<p><strong>Valid</strong>: </p>
								<p><strong>All members share: {group.common_time_slots.map(formatSlot).join(', ')}</strong></p>
							</span>
						</div>
					{/if}

					{#if error}
						<p class="text-error text-sm mb-2">{error}</p>
					{/if}
					{#if successMsg}
						<p class="text-success text-sm mb-2">{successMsg}</p>
					{/if}

					<div class="divider my-2"></div>
					<h2 class="font-semibold mb-2">Members ({group.members.length}/5)</h2>
					<ul class="divide-y divide-base-200">
						{#each group.members as member}
							<li class="py-2 text-sm flex items-center gap-2">
								{member.first_name}
								{member.last_name}
								{#if member.id === $user?.id}
									<span class="badge badge-ghost badge-sm">you</span>
								{/if}
							</li>
						{/each}
					</ul>

					<div class="divider my-2"></div>
					<button
						class="btn btn-outline btn-error btn-sm self-start"
						onclick={leaveGroup}
						disabled={leaving}
					>
						{leaving ? 'Leaving…' : 'Leave Group'}
					</button>
				</div>
			</div>
		{/if}
	</div>
{/if}
