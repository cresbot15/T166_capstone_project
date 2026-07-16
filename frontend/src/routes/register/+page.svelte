<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { token, user } from '$lib/stores';
	import { DAYS, PERIODS } from '$lib/timeslots';

	let firstName = $state('');
	let lastName = $state('');
	let email = $state('');
	let password = $state('');
	let isNewStudent = $state(true);
	let deliveryMode = $state('Online');
	let skills = $state('');
	let selectedSlots = $state(new Set<string>());
	let error = $state('');
	let loading = $state(false);

	onMount(() => {
		if ($token) goto('/profile');
	});

	function toggleSlot(slot: string) {
		const next = new Set(selectedSlots);
		if (next.has(slot)) next.delete(slot);
		else next.add(slot);
		selectedSlots = next;
	}

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		loading = true;
		try {
			await api.register({
				first_name: firstName,
				last_name: lastName,
				email,
				password,
				is_new_student: isNewStudent,
				delivery_mode: deliveryMode,
				skills: skills || null,
				time_preferences: [...selectedSlots]
			});
			const loginData = await api.login(email, password);
			token.set(loginData.access_token);
			const me = await api.getMe();
			user.set(me);
			goto('/profile');
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Registration failed';
		} finally {
			loading = false;
		}
	}
</script>

<div class="bg-base-200 min-h-screen py-10 px-4">
	<div class="card bg-base-100 shadow w-full max-w-xl mx-auto">
		<div class="card-body">
			<h1 class="card-title text-xl mb-2">Register</h1>
			<form onsubmit={handleSubmit} class="flex flex-col gap-3">
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
					<span class="text-sm font-medium">Email</span>
					<input type="email" class="input input-bordered" bind:value={email} required />
				</label>

				<label class="flex flex-col gap-1">
					<span class="text-sm font-medium">Password</span>
					<input type="password" class="input input-bordered" bind:value={password} required />
				</label>

				<div class="flex flex-col gap-2">
					<span class="text-sm font-medium">Student Type</span>
					<div class="flex gap-6">
						<label class="flex items-center gap-2 text-sm cursor-pointer">
							<input type="radio" class="radio radio-sm" bind:group={isNewStudent} value={true} />
							New Student
						</label>
						<label class="flex items-center gap-2 text-sm cursor-pointer">
							<input type="radio" class="radio radio-sm" bind:group={isNewStudent} value={false} />
							Continuing Student
						</label>
					</div>
				</div>

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

				<button type="submit" class="btn btn-primary mt-1" disabled={loading}>
					{loading ? 'Registering…' : 'Register'}
				</button>
			</form>
			<p class="text-sm text-base-content/60 mt-2">
				Already have an account? <a href="/" class="link">Sign In</a>
			</p>
		</div>
	</div>
</div>
