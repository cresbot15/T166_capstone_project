<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { token, activeUnit } from '$lib/stores';
	import { defaultTimeSlots } from '$lib/timeslots';

	let mode = $state<'join' | 'create'>('join');
	let code = $state('');
	let unitName = $state('');
	let error = $state('');
	let loading = $state(false);

	onMount(() => {
		if (!$token) goto('/');
	});

	async function handleJoin(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		loading = true;
		try {
			const unit = await api.joinUnit(code);
			activeUnit.set(unit);
			goto('/onboarding/setup');
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Could not join unit';
		} finally {
			loading = false;
		}
	}

	async function handleCreate(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		loading = true;
		try {
			const unit = await api.createUnit(unitName || undefined, defaultTimeSlots());
			activeUnit.set(unit);
			goto('/onboarding/setup');
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Could not create unit';
		} finally {
			loading = false;
		}
	}
</script>

<div class="min-h-screen flex items-center justify-center px-4">
	<div class="card bg-base-100 shadow-sm rounded-2xl w-full max-w-md">
		<div class="card-body">
			<h1 class="text-2xl font-extrabold text-primary mb-1">Join or Create a Unit</h1>
			<p class="text-sm text-base-content/60 mb-4">
				Enter a unit code to join, or create a new unit.
			</p>

			<div role="tablist" class="tabs tabs-boxed mb-4">
				<button
					type="button"
					role="tab"
					class="tab {mode === 'join' ? 'tab-active' : ''}"
					onclick={() => (mode = 'join')}
				>
					Join a Unit
				</button>
				<button
					type="button"
					role="tab"
					class="tab {mode === 'create' ? 'tab-active' : ''}"
					onclick={() => (mode = 'create')}
				>
					Create a Unit
				</button>
			</div>

			{#if mode === 'join'}
				<form onsubmit={handleJoin} class="flex flex-col gap-3">
					<label class="flex flex-col gap-1">
						<span class="text-sm font-medium">Unit Code</span>
						<input
							type="text"
							class="input input-bordered"
							bind:value={code}
							placeholder="e.g. IFB398"
							required
						/>
					</label>
					{#if error}<p class="text-error text-sm">{error}</p>{/if}
					<button type="submit" class="btn btn-primary mt-1" disabled={loading}>
						{loading ? 'Joining…' : 'Join Unit'}
					</button>
				</form>
			{:else}
				<form onsubmit={handleCreate} class="flex flex-col gap-3">
					<label class="flex flex-col gap-1">
						<span class="text-sm font-medium"
							>Unit Name <span class="text-base-content/50 font-normal">(optional)</span></span
						>
						<input
							type="text"
							class="input input-bordered"
							bind:value={unitName}
							placeholder="e.g. IFB398 Capstone"
						/>
					</label>
					{#if error}<p class="text-error text-sm">{error}</p>{/if}
					<button type="submit" class="btn btn-primary mt-1" disabled={loading}>
						{loading ? 'Creating…' : 'Create Unit'}
					</button>
				</form>
			{/if}
		</div>
	</div>
</div>
