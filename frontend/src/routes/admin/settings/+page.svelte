<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { token, activeUnit } from '$lib/stores';
	import { api } from '$lib/api';
	import PageHeader from '$lib/components/PageHeader.svelte';

	let isOwner = $state(false);
	let loadError = $state('');
	let saveError = $state('');
	let saving = $state(false);

	let originalStart = $state('');
	let originalEnd = $state('');
	let formationStart = $state('');
	let formationEnd = $state('');
	let editingStart = $state(false);
	let editingEnd = $state(false);

	const hasPendingChanges = $derived(
		formationStart !== originalStart || formationEnd !== originalEnd
	);

	function isoToDatetimeLocal(iso: string | null): string {
		if (!iso) return '';
		const d = new Date(iso);
		const pad = (n: number) => String(n).padStart(2, '0');
		return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
	}

	function datetimeLocalToIso(value: string): string | null {
		return value ? new Date(value).toISOString() : null;
	}

	function todayAt(time: string): string {
		const d = new Date();
		const pad = (n: number) => String(n).padStart(2, '0');
		return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${time}`;
	}

	function startEditingStart() {
		editingStart = true;
		if (!formationStart) formationStart = todayAt('00:00');
	}

	function startEditingEnd() {
		editingEnd = true;
		if (!formationEnd) formationEnd = todayAt('23:59');
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
			if (profile.role !== 'owner') {
				goto('/home');
				return;
			}
			isOwner = true;
		} catch {
			goto('/home');
			return;
		}

		originalStart = isoToDatetimeLocal($activeUnit.formation_start_date);
		originalEnd = isoToDatetimeLocal($activeUnit.formation_end_date);
		formationStart = originalStart;
		formationEnd = originalEnd;
		editingStart = originalStart !== '';
		editingEnd = originalEnd !== '';
	});

	function discardChanges() {
		formationStart = originalStart;
		formationEnd = originalEnd;
		editingStart = originalStart !== '';
		editingEnd = originalEnd !== '';
		saveError = '';
	}

	function clearStart() {
		formationStart = '';
		editingStart = false;
	}

	function clearEnd() {
		formationEnd = '';
		editingEnd = false;
	}

	async function saveChanges() {
		if (!$activeUnit) return;
		if (!confirm('Save changes to this unit\'s settings?')) return;

		saveError = '';
		saving = true;
		try {
			const updated = await api.setFormationWindow($activeUnit.id, {
				formationStartDate: datetimeLocalToIso(formationStart),
				formationEndDate: datetimeLocalToIso(formationEnd)
			});
			activeUnit.set(updated);
			originalStart = isoToDatetimeLocal(updated.formation_start_date);
			originalEnd = isoToDatetimeLocal(updated.formation_end_date);
			formationStart = originalStart;
			formationEnd = originalEnd;
			editingStart = originalStart !== '';
			editingEnd = originalEnd !== '';
		} catch (e: unknown) {
			saveError = e instanceof Error ? e.message : 'Could not save unit settings';
		} finally {
			saving = false;
		}
	}
</script>

<PageHeader
	title="Unit Settings"
	subtitle={`Settings for ${$activeUnit?.name ?? $activeUnit?.code ?? ''}`}
/>

<div class="max-w-xl mx-auto px-4 py-8">
	{#if loadError}<p class="text-error text-sm mb-2">{loadError}</p>{/if}
	{#if saveError}<p class="text-error text-sm mb-2">{saveError}</p>{/if}

	{#if isOwner}
		<div class="card bg-base-100 shadow-sm rounded-2xl">
			<div class="card-body">
				<h2 class="font-bold mb-1">Group Formation Window</h2>
				<p class="text-sm text-base-content/60 mb-3">
					Controls when students can create, join, or leave groups in this unit. Leave either
					blank to leave that end open.
				</p>
				<div class="grid grid-cols-2 gap-3">
					<div class="flex flex-col gap-1">
						<span class="text-sm font-medium">Formation opens</span>
						{#if editingStart}
							<input
								type="datetime-local"
								class="input input-bordered"
								bind:value={formationStart}
							/>
							<button
								type="button"
								class="text-xs text-error self-start mt-0.5"
								onclick={clearStart}
							>
								Clear
							</button>
						{:else}
							<div class="flex items-center gap-2">
								<span class="text-sm text-base-content/50 italic">No date set</span>
								<button type="button" class="btn btn-ghost btn-xs" onclick={startEditingStart}>
									Set a date
								</button>
							</div>
						{/if}
					</div>
					<div class="flex flex-col gap-1">
						<span class="text-sm font-medium">Formation closes</span>
						{#if editingEnd}
							<input type="datetime-local" class="input input-bordered" bind:value={formationEnd} />
							<button type="button" class="text-xs text-error self-start mt-0.5" onclick={clearEnd}>
								Clear
							</button>
						{:else}
							<div class="flex items-center gap-2">
								<span class="text-sm text-base-content/50 italic">No date set</span>
								<button type="button" class="btn btn-ghost btn-xs" onclick={startEditingEnd}>
									Set a date
								</button>
							</div>
						{/if}
					</div>
				</div>
			</div>
		</div>

		<div class="card bg-base-100 shadow-sm rounded-2xl mt-4">
			<div class="card-body">
				<h2 class="font-bold mb-1">Transfer Ownership</h2>
				<p class="text-sm text-base-content/60 mb-3">
					Make another administrator the owner of this unit. You will be demoted to
					administrator once the transfer completes.
				</p>
				<a href="/admin/settings/transfer-owner" class="btn btn-outline btn-sm self-start">
					Transfer Ownership
				</a>
			</div>
		</div>

		<div class="sticky bottom-4 mt-6 flex justify-end gap-2">
			<button
				type="button"
				class="btn btn-ghost btn-sm"
				disabled={saving || !hasPendingChanges}
				onclick={discardChanges}
			>
				Discard changes
			</button>
			<button
				type="button"
				class="btn btn-primary btn-sm"
				disabled={saving || !hasPendingChanges}
				onclick={saveChanges}
			>
				{saving ? 'Saving…' : 'Save changes'}
			</button>
		</div>
	{/if}
</div>
