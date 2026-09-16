<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { token, activeUnit, unitRole } from '$lib/stores';
	import { api, type UnitMemberResponse } from '$lib/api';
	import PageHeader from '$lib/components/PageHeader.svelte';

	type Step = 'intro' | 'select' | 'confirm' | 'done';

	let step = $state<Step>('intro');
	let loading = $state(true);
	let loadError = $state('');
	let transferError = $state('');
	let transferring = $state(false);

	let administrators = $state<UnitMemberResponse[]>([]);
	let selectedUserId = $state<number | null>(null);

	const selectedAdministrator = $derived(
		administrators.find((m) => m.user_id === selectedUserId) ?? null
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
			if (profile.role !== 'owner') {
				goto('/home');
				return;
			}
		} catch {
			goto('/home');
			return;
		}
		try {
			const members = await api.getUnitMembers($activeUnit.id);
			administrators = members.filter((m) => m.role === 'administrator');
		} catch (e: unknown) {
			loadError = e instanceof Error ? e.message : 'Could not load members';
		} finally {
			loading = false;
		}
	});

	function goToSelect() {
		step = 'select';
	}

	function selectAdministrator(userId: number) {
		selectedUserId = userId;
	}

	function goToConfirm() {
		if (!selectedUserId) return;
		step = 'confirm';
	}

	async function confirmTransfer() {
		if (!$activeUnit || !selectedAdministrator) return;
		if (
			!confirm(
				`Are you absolutely sure you want to transfer ownership to ${selectedAdministrator.first_name} ${selectedAdministrator.last_name}? This cannot be undone by you alone.`
			)
		) {
			return;
		}

		transferError = '';
		transferring = true;
		try {
			await api.transferOwnership($activeUnit.id, selectedAdministrator.user_id);
			unitRole.set('administrator');
			step = 'done';
		} catch (e: unknown) {
			transferError = e instanceof Error ? e.message : 'Could not transfer ownership';
		} finally {
			transferring = false;
		}
	}
</script>

<PageHeader title="Transfer Ownership" subtitle={$activeUnit?.name ?? $activeUnit?.code ?? ''} />

<div class="max-w-xl mx-auto px-4 py-8">
	{#if loading}
		<span class="loading loading-spinner"></span>
	{:else if loadError}
		<p class="text-error text-sm">{loadError}</p>
	{:else if step === 'intro'}
		<div class="card bg-base-100 shadow-sm rounded-2xl">
			<div class="card-body gap-3">
				<h2 class="font-bold">What this does</h2>
				<p class="text-sm text-base-content/70">
					Transferring ownership makes another administrator the owner of this unit. The new
					owner will get full control over unit settings, including the group formation window,
					member roles, and group management.
				</p>
				<p class="text-sm text-base-content/70">
					You will be demoted to administrator once the transfer completes. This can only be
					undone if the new owner transfers ownership back to you.
				</p>
				<div class="flex justify-end gap-2 mt-2">
					<a href="/admin/settings" class="btn btn-ghost btn-sm">Cancel</a>
					<button type="button" class="btn btn-primary btn-sm" onclick={goToSelect}>
						Continue
					</button>
				</div>
			</div>
		</div>
	{:else if step === 'select'}
		<div class="card bg-base-100 shadow-sm rounded-2xl">
			<div class="card-body gap-3">
				<h2 class="font-bold">Choose the new owner</h2>
				<p class="text-sm text-base-content/60">
					Only this unit's administrators can be selected. Promote a student to administrator
					first from Manage Members if the person you want isn't listed.
				</p>

				{#if administrators.length === 0}
					<p class="text-sm text-base-content/60 italic">
						There are no administrators in this unit yet.
					</p>
					<a href="/admin/members" class="btn btn-outline btn-sm self-start">
						Go to Manage Members
					</a>
				{:else}
					<div class="flex flex-col gap-2">
						{#each administrators as admin}
							<button
								type="button"
								class="card bg-base-200 rounded-xl text-left transition-colors {selectedUserId ===
								admin.user_id
									? 'ring-2 ring-primary'
									: ''}"
								onclick={() => selectAdministrator(admin.user_id)}
							>
								<div class="card-body p-3">
									<p class="font-medium">{admin.first_name} {admin.last_name}</p>
									<p class="text-xs text-base-content/60">{admin.email}</p>
								</div>
							</button>
						{/each}
					</div>
				{/if}

				<div class="flex justify-end gap-2 mt-2">
					<button type="button" class="btn btn-ghost btn-sm" onclick={() => (step = 'intro')}>
						Back
					</button>
					<button
						type="button"
						class="btn btn-primary btn-sm"
						disabled={!selectedUserId}
						onclick={goToConfirm}
					>
						Continue
					</button>
				</div>
			</div>
		</div>
	{:else if step === 'confirm' && selectedAdministrator}
		<div class="card bg-base-100 shadow-sm rounded-2xl">
			<div class="card-body gap-3">
				<h2 class="font-bold">Confirm transfer</h2>
				<p class="text-sm text-base-content/70">
					You're about to make
					<span class="font-medium"
						>{selectedAdministrator.first_name} {selectedAdministrator.last_name}</span
					>
					the owner of this unit. You will be demoted to administrator, and the new owner will
					have full control over unit settings.
				</p>
				{#if transferError}<p class="text-error text-sm">{transferError}</p>{/if}
				<div class="flex justify-end gap-2 mt-2">
					<button
						type="button"
						class="btn btn-ghost btn-sm"
						disabled={transferring}
						onclick={() => (step = 'select')}
					>
						Back
					</button>
					<button
						type="button"
						class="btn btn-error btn-sm"
						disabled={transferring}
						onclick={confirmTransfer}
					>
						{transferring ? 'Transferring…' : 'Confirm Transfer'}
					</button>
				</div>
			</div>
		</div>
	{:else if step === 'done' && selectedAdministrator}
		<div class="card bg-base-100 shadow-sm rounded-2xl">
			<div class="card-body gap-3">
				<h2 class="font-bold">Ownership transferred</h2>
				<p class="text-sm text-base-content/70">
					{selectedAdministrator.first_name} {selectedAdministrator.last_name} is now the owner of
					this unit. You are now an administrator.
				</p>
				<a href="/admin/members" class="btn btn-primary btn-sm self-start">
					Back to Manage Members
				</a>
			</div>
		</div>
	{/if}
</div>
