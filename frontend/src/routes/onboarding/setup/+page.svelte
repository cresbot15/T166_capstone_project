<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { token, activeUnit } from '$lib/stores';
	import TimeGrid from '$lib/components/TimeGrid.svelte';

	let deliveryMode = $state('Online');
	let skills = $state('');
	let selectedSlots = $state(new Set<string>());
	let error = $state('');
	let loading = $state(false);

	onMount(() => {
		if (!$token) {
			goto('/');
			return;
		}
		if (!$activeUnit) {
			goto('/onboarding/unit');
		}
	});

	function toggleSlot(slot: string) {
		const next = new Set(selectedSlots);
		if (next.has(slot)) next.delete(slot);
		else next.add(slot);
		selectedSlots = next;
	}

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		if (!$activeUnit) return;
		error = '';
		loading = true;
		try {
			await api.updateMyUnitProfile($activeUnit.id, {
				delivery_mode: deliveryMode,
				skills: skills || undefined,
				time_preferences: [...selectedSlots]
			});
			goto('/home');
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Could not save your details';
		} finally {
			loading = false;
		}
	}
</script>

<div class="min-h-screen flex items-center justify-center px-4 py-10">
	<div class="card bg-base-100 shadow-sm rounded-2xl w-full max-w-xl">
		<div class="card-body">
			<h1 class="text-2xl font-extrabold text-primary mb-1">Set Up Your Profile</h1>
			<p class="text-sm text-base-content/60 mb-4">
				Tell {$activeUnit?.name ?? $activeUnit?.code} a bit about how you'll be studying.
			</p>
			<form onsubmit={handleSubmit} class="flex flex-col gap-4">
				<div class="flex flex-col gap-2">
					<span class="text-sm font-medium">Delivery Mode</span>
					<div class="flex gap-6">
						<label class="flex items-center gap-2 text-sm cursor-pointer">
							<input type="radio" class="radio radio-sm" bind:group={deliveryMode} value="Online" />
							Online
						</label>
						<label class="flex items-center gap-2 text-sm cursor-pointer">
							<input
								type="radio"
								class="radio radio-sm"
								bind:group={deliveryMode}
								value="In-person"
							/>
							In-person
						</label>
					</div>
				</div>

				<label class="flex flex-col gap-1">
					<span class="text-sm font-medium">
						Skills <span class="text-base-content/50 font-normal">(optional)</span>
					</span>
					<input
						type="text"
						class="input input-bordered"
						bind:value={skills}
						placeholder="e.g. Python, React, UI Design"
					/>
				</label>

				<div class="flex flex-col gap-2">
					<span class="text-sm font-medium">Availability</span>
					<TimeGrid selected={selectedSlots} onToggle={toggleSlot} />
				</div>

				<!--
					TODO: admin-defined per-unit questions would render here once a
					custom-question backend feature exists (see docs/superpowers/specs/
					2026-08-08-frontend-ui-rework-design.md, Non-goals). No component yet —
					this comment is the intended insertion point.
				-->

				{#if error}<p class="text-error text-sm">{error}</p>{/if}

				<button type="submit" class="btn btn-primary mt-1" disabled={loading}>
					{loading ? 'Saving…' : 'Finish Setup'}
				</button>
			</form>
		</div>
	</div>
</div>
