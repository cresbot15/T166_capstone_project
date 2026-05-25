<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { token, user } from '$lib/stores';
	import { DAYS, PERIODS } from '$lib/timeslots';

	let loading = $state(true);
	let saving = $state(false);
	let editMode = $state(false);
	let error = $state('');
	let successMsg = $state('');

	let firstName = $state('');
	let lastName = $state('');
	let deliveryMode = $state('');
	let skills = $state('');
	let selectedSlots = $state(new Set<string>());

	onMount(async () => {
		if (!$token) {
			goto('/');
			return;
		}
		try {
			const me = await api.getMe();
			user.set(me);
			syncForm(me);
		} catch {
			token.clear();
			goto('/');
		} finally {
			loading = false;
		}
	});

	function syncForm(u: NonNullable<typeof $user>) {
		firstName = u.first_name;
		lastName = u.last_name;
		deliveryMode = u.delivery_mode ?? 'Online';
		skills = u.skills ?? '';
		selectedSlots = new Set(u.time_preferences);
	}

	function startEdit() {
		if ($user) syncForm($user);
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

	async function saveProfile(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		saving = true;
		try {
			const updated = await api.updateMe({
				first_name: firstName,
				last_name: lastName,
				delivery_mode: deliveryMode,
				skills: skills || null,
				time_preferences: [...selectedSlots]
			});
			user.set(updated);
			editMode = false;
			successMsg = 'Profile updated.';
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Update failed';
		} finally {
			saving = false;
		}
	}
</script>

{#if loading}
	<div class="max-w-xl mx-auto py-10 px-4">
		<span class="loading loading-spinner"></span>
	</div>
{:else if $user}
	<div class="max-w-xl mx-auto py-8 px-4">
		<div class="card bg-base-100 border border-base-300 shadow-sm">
			<div class="card-body">
				{#if !editMode}
					<div class="flex items-center justify-between mb-4">
						<h1 class="text-xl font-semibold">{$user.first_name} {$user.last_name}</h1>
						<button class="btn btn-ghost btn-sm" onclick={startEdit}>Edit</button>
					</div>

					<dl class="grid grid-cols-[120px_1fr] gap-x-4 gap-y-2 text-sm mb-4">
						<dt class="text-base-content/60">Email</dt>
						<dd>{$user.email}</dd>
						<dt class="text-base-content/60">Student Type</dt>
						<dd>{$user.is_new_student ? 'New Student' : 'Continuing Student'}</dd>
						<dt class="text-base-content/60">Delivery Mode</dt>
						<dd>{$user.delivery_mode ?? '—'}</dd>
					</dl>

					<div class="mb-4">
						<p class="text-sm text-base-content/60 mb-1">Skills</p>
						<p class="text-sm whitespace-pre-wrap">{$user.skills ?? '—'}</p>
					</div>

					<div class="divider my-3"></div>
					<h2 class="font-semibold mb-3">Availability</h2>

					{#if $user.time_preferences.length > 0}
						<table class="table table-sm">
							<thead>
								<tr>
									<th></th>
									{#each PERIODS as period}
										<th class="text-center font-medium text-base-content/60">{period}</th>
									{/each}
								</tr>
							</thead>
							<tbody>
								{#each DAYS as day}
									<tr>
										<td class="text-sm text-base-content/70 pr-4">
											{day.charAt(0).toUpperCase() + day.slice(1)}
										</td>
										{#each PERIODS as period}
											{@const slot = `${day}${period}`}
											{@const selected = $user.time_preferences.includes(slot)}
											<td class="text-center text-sm {selected ? 'text-primary font-semibold' : 'text-base-content/20'}">
												{selected ? '✓' : '·'}
											</td>
										{/each}
									</tr>
								{/each}
							</tbody>
						</table>
					{:else}
						<p class="text-sm text-base-content/60">No availability set yet.</p>
					{/if}

					{#if successMsg}
						<p class="text-success text-sm mt-3">{successMsg}</p>
					{/if}

					<div class="divider my-3"></div>
					<div class="flex items-center gap-2 text-sm">
						<span class="text-base-content/60">Group:</span>
						{#if $user.group_id}
							<a href="/group" class="link">View my group →</a>
						{:else}
							<span class="text-base-content/60">Not in a group.</span>
							<a href="/group" class="link">Join one →</a>
						{/if}
					</div>
				{:else}
					<h1 class="text-xl font-semibold mb-4">Edit Profile</h1>
					<form onsubmit={saveProfile} class="flex flex-col gap-3">
						<div class="grid grid-cols-2 gap-3">
							<label class="flex flex-col gap-1">
								<span class="text-sm font-medium">First Name</span>
								<input type="text" class="input input-bordered" bind:value={firstName} required />
							</label>
							<label class="flex flex-col gap-1">
								<span class="text-sm font-medium">Last Name</span>
								<input type="text" class="input input-bordered" bind:value={lastName} required />
							</label>
						</div>

						<label class="flex flex-col gap-1">
							<span class="text-sm font-medium">Delivery Mode</span>
							<select class="select select-bordered" bind:value={deliveryMode}>
								<option value="Online">Online</option>
								<option value="In-person">In-person</option>
							</select>
						</label>

						<label class="flex flex-col gap-1">
							<span class="text-sm font-medium">Skills</span>
							<textarea class="textarea textarea-bordered" bind:value={skills} rows={3}></textarea>
						</label>

						<div class="flex flex-col gap-2">
							<span class="text-sm font-medium">Availability</span>
							<table class="table table-sm">
								<thead>
									<tr>
										<th></th>
										{#each PERIODS as period}
											<th class="text-center font-medium text-base-content/60">{period}</th>
										{/each}
									</tr>
								</thead>
								<tbody>
									{#each DAYS as day}
										<tr>
											<td class="text-sm text-base-content/70 pr-4">
												{day.charAt(0).toUpperCase() + day.slice(1)}
											</td>
											{#each PERIODS as period}
												{@const slot = `${day}${period}`}
												<td class="text-center">
													<input
														type="checkbox"
														class="checkbox checkbox-sm checkbox-primary"
														checked={selectedSlots.has(slot)}
														onchange={() => toggleSlot(slot)}
													/>
												</td>
											{/each}
										</tr>
									{/each}
								</tbody>
							</table>
						</div>

						{#if error}
							<p class="text-error text-sm">{error}</p>
						{/if}

						<div class="flex gap-2 mt-1">
							<button type="submit" class="btn btn-primary btn-sm" disabled={saving}>
								{saving ? 'Saving…' : 'Save'}
							</button>
							<button type="button" class="btn btn-ghost btn-sm" onclick={cancelEdit}>Cancel</button>
						</div>
					</form>
				{/if}
			</div>
		</div>
	</div>
{/if}
