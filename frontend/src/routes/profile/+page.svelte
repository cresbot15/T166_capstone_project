<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api, type GroupResponse, type UnitMeResponse } from '$lib/api';
	import { token, user, activeUnit } from '$lib/stores';
	import TimeGrid from '$lib/components/TimeGrid.svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import SectionCard from '$lib/components/SectionCard.svelte';

	let loading = $state(true);
	let saving = $state(false);
	let editMode = $state(false);
	let error = $state('');
	let successMsg = $state('');

	let unitProfile = $state<UnitMeResponse | null>(null);
	let myGroup = $state<GroupResponse | null>(null);

	let deliveryMode = $state('Online');
	let skills = $state('');
	let selectedSlots = $state(new Set<string>());

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
			unitProfile = await api.getMyUnitProfile($activeUnit.id);
			syncForm(unitProfile);
			const groups = await api.getMyGroups();
			myGroup = groups.find((g) => g.unit_id === $activeUnit!.id) ?? null;
		} catch {
			error = 'Could not load your profile for this unit';
		} finally {
			loading = false;
		}
	});

	function syncForm(p: UnitMeResponse) {
		deliveryMode = p.delivery_mode ?? 'Online';
		skills = p.skills ?? '';
		selectedSlots = new Set(p.time_preferences);
	}

	function startEdit() {
		if (unitProfile) syncForm(unitProfile);
		successMsg = '';
		editMode = true;
	}

	function cancelEdit() {
		editMode = false;
		error = '';
	}

	function toggleSlot(slot: string) {
		const next = new Set(selectedSlots);
		if (next.has(slot)) next.delete(slot);
		else next.add(slot);
		selectedSlots = next;
	}

	function logout() {
		token.clear();
		user.set(null);
		activeUnit.clear();
		goto('/');
	}

	async function saveProfile(e: SubmitEvent) {
		e.preventDefault();
		if (!$activeUnit) return;
		error = '';
		saving = true;
		try {
			unitProfile = await api.updateMyUnitProfile($activeUnit.id, {
				delivery_mode: deliveryMode,
				skills: skills || undefined,
				time_preferences: [...selectedSlots]
			});
			editMode = false;
			successMsg = 'Profile updated.';
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Update failed';
		} finally {
			saving = false;
		}
	}
</script>

<PageHeader title={`Welcome, ${$user?.first_name ?? ''}!`} subtitle={$user?.email ?? ''}>
	{#snippet actions()}
		{#if !editMode}
			<button class="btn btn-outline btn-sm" onclick={startEdit}>Edit Profile</button>
		{/if}
		<button class="btn btn-ghost btn-sm" onclick={logout}>Logout</button>
	{/snippet}
</PageHeader>

<div class="max-w-3xl mx-auto px-4 py-8">
	{#if loading}
		<span class="loading loading-spinner"></span>
	{:else if editMode}
		<SectionCard title="Edit Profile">
			<form onsubmit={saveProfile} class="flex flex-col gap-3">
				<div class="flex flex-col gap-2">
					<span class="text-sm font-medium">Delivery Mode</span>
					<select class="select select-bordered" bind:value={deliveryMode}>
						<option value="Online">Online</option>
						<option value="In-person">In-person</option>
					</select>
				</div>
				<label class="flex flex-col gap-1">
					<span class="text-sm font-medium">Skills</span>
					<textarea class="textarea textarea-bordered" bind:value={skills} rows={3}></textarea>
				</label>
				<div class="flex flex-col gap-2">
					<span class="text-sm font-medium">Availability</span>
					<TimeGrid selected={selectedSlots} onToggle={toggleSlot} />
				</div>
				{#if error}<p class="text-error text-sm">{error}</p>{/if}
				<div class="flex gap-2 mt-1">
					<button type="submit" class="btn btn-primary btn-sm" disabled={saving}>
						{saving ? 'Saving…' : 'Save'}
					</button>
					<button type="button" class="btn btn-ghost btn-sm" onclick={cancelEdit}>Cancel</button>
				</div>
			</form>
		</SectionCard>
	{:else}
		<div class="grid gap-4 md:grid-cols-2">
			<SectionCard title="Your Schedule">
				<p class="text-sm text-base-content/60 mb-3">
					Times you've indicated you're available to meet.
				</p>
				<TimeGrid selected={new Set(unitProfile?.time_preferences ?? [])} readonly />
			</SectionCard>

			<SectionCard title="Profile Details">
				<dl class="flex flex-col gap-2 text-sm">
					<div>
						<dt class="text-base-content/60">Delivery Mode</dt>
						<dd>{unitProfile?.delivery_mode ?? '—'}</dd>
					</div>
					<div>
						<dt class="text-base-content/60">Skills</dt>
						<dd class="whitespace-pre-wrap">{unitProfile?.skills ?? '—'}</dd>
					</div>
				</dl>
			</SectionCard>

			<div class="md:col-span-2">
				<SectionCard title="Your Team">
					{#if successMsg}<p class="text-success text-sm mb-2">{successMsg}</p>{/if}
					{#if myGroup}
						<p class="text-sm">
							You're in Group {myGroup.id} with {myGroup.members.length} member{myGroup.members
								.length !== 1
								? 's'
								: ''}.
							<a href="/group" class="link">View your group →</a>
						</p>
					{:else}
						<p class="text-sm text-base-content/60">
							You haven't joined a group yet. <a href="/group" class="link">Create or join one →</a>
						</p>
					{/if}
				</SectionCard>
			</div>
		</div>
	{/if}
</div>
