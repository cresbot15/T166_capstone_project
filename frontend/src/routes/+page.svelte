<script lang="ts">
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { token, user, activeUnit } from '$lib/stores';

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
			const data = await api.login(email, password);
			token.set(data.access_token);
			user.set(await api.getMe());

			const units = await api.getMyUnits();
			if (units.length === 0) {
				goto('/onboarding/unit');
				return;
			}
			const current = get(activeUnit);
			const stillValid = current && units.some((u) => u.id === current.id);
			activeUnit.set(stillValid ? current : units[0]);
			goto('/home');
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Login failed';
		} finally {
			loading = false;
		}
	}
</script>

<div class="min-h-screen flex items-center justify-center px-4">
	<div class="card bg-base-100 shadow-sm rounded-2xl w-full max-w-sm">
		<div class="card-body">
			<h1 class="text-2xl font-extrabold text-primary mb-1">Sign In</h1>
			<p class="text-sm text-base-content/60 mb-4">Welcome back to TeamUp!</p>
			<form onsubmit={handleSubmit} class="flex flex-col gap-3">
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
					{loading ? 'Signing in…' : 'Sign In'}
				</button>
			</form>
			<p class="text-sm text-base-content/60 mt-3">
				No account? <a href="/register" class="link">Register</a>
			</p>
		</div>
	</div>
</div>
