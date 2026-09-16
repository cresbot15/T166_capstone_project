<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { token, user } from '$lib/stores';

	let step = $state<'role' | 'form'>('role');
	let role = $state<'student' | 'unit_coordinator'>('student');

	let firstName = $state('');
	let lastName = $state('');
	let email = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	onMount(() => {
		if ($token) goto('/home');
	});

	function chooseRole(chosen: 'student' | 'unit_coordinator') {
		role = chosen;
		step = 'form';
	}

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		loading = true;
		try {
			await api.register({ first_name: firstName, last_name: lastName, email, password, role });
			const loginData = await api.login(email, password);
			token.set(loginData.access_token);
			user.set(await api.getMe());
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
			{#if step === 'role'}
				<h1 class="text-2xl font-extrabold text-primary mb-1">Register an Account</h1>
				<p class="text-sm text-base-content/60 mb-4">
					Are you registering as a student, or as a member of teaching staff?
				</p>
				<div class="flex flex-col gap-3">
					<button
						type="button"
						class="btn btn-outline btn-block h-auto py-4 flex-col items-start gap-0.5 text-left normal-case"
						onclick={() => chooseRole('student')}
					>
						<span class="font-bold">Student</span>
						<span class="text-sm text-base-content/60 font-normal">
							Join a unit and form project groups
						</span>
					</button>
					<button
						type="button"
						class="btn btn-outline btn-block h-auto py-4 flex-col items-start gap-0.5 text-left normal-case"
						onclick={() => chooseRole('unit_coordinator')}
					>
						<span class="font-bold">Teaching Staff</span>
						<span class="text-sm text-base-content/60 font-normal">
							Create and manage units
						</span>
					</button>
				</div>
			{:else}
				<button
					type="button"
					class="link text-sm self-start mb-2"
					onclick={() => (step = 'role')}
				>
					← Back
				</button>
				<h1 class="text-2xl font-extrabold text-primary mb-1">Register an Account</h1>
				<p class="text-sm text-base-content/60 mb-4">
					Registering as <span class="font-semibold">
						{role === 'student' ? 'a Student' : 'Teaching Staff'}
					</span>.
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
					{#if error}<p class="text-error text-sm">{error}</p>{/if}
					<button type="submit" class="btn btn-primary mt-1" disabled={loading}>
						{loading ? 'Registering…' : 'Register'}
					</button>
				</form>
			{/if}
			<p class="text-sm text-base-content/60 mt-3">
				Already have an account? <a href="/" class="link">Sign In</a>
			</p>
		</div>
	</div>
</div>
