<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { token } from '$lib/stores';

	let firstName = $state('');
	let lastName = $state('');
	let email = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	onMount(() => {
		if ($token) goto('/home');
	});

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		loading = true;
		try {
			await api.register({ first_name: firstName, last_name: lastName, email, password });
			const loginData = await api.login(email, password);
			token.set(loginData.access_token);
			goto('/onboarding/unit');
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Registration failed';
		} finally {
			loading = false;
		}
	}
</script>

<div class="min-h-screen flex items-center justify-center px-4">
	<div class="card bg-base-100 shadow-sm rounded-2xl w-full max-w-md">
		<div class="card-body">
			<h1 class="text-2xl font-extrabold text-primary mb-1">Register an Account</h1>
			<p class="text-sm text-base-content/60 mb-4">
				Please fill out the following form to register with TeamUp.
			</p>
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
				{#if error}
					<p class="text-error text-sm">{error}</p>
				{/if}
				<button type="submit" class="btn btn-primary mt-1" disabled={loading}>
					{loading ? 'Registering…' : 'Register'}
				</button>
			</form>
			<p class="text-sm text-base-content/60 mt-3">
				Already have an account? <a href="/" class="link">Sign In</a>
			</p>
		</div>
	</div>
</div>
