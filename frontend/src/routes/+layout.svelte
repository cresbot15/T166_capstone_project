<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { token, user, activeUnit } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { api, type UnitResponse } from '$lib/api';
	import UnitSwitcher from '$lib/components/UnitSwitcher.svelte';
	import type { Snippet } from 'svelte';

	let { children }: { children: Snippet } = $props();

	let myUnits = $state<UnitResponse[]>([]);

	onMount(async () => {
		if (!$token) return;
		if (!$user) {
			try {
				$user = await api.getMe();
			} catch {
				token.clear();
				goto('/');
				return;
			}
		}
		myUnits = await api.getMyUnits();
	});

	function logout() {
		token.clear();
		user.set(null);
		activeUnit.clear();
		goto('/');
	}

	function switchUnit(unit: UnitResponse) {
		activeUnit.set(unit);
		goto('/home');
	}
</script>

{#if $token}
	<div class="navbar bg-primary text-primary-content px-4">
		<div class="navbar-start gap-2">
			<span class="font-extrabold text-lg">TeamUp!</span>
			<UnitSwitcher units={myUnits} activeUnitId={$activeUnit?.id ?? null} onSwitch={switchUnit} />
		</div>
		<div class="navbar-center gap-1">
			<a
				href="/home"
				class="btn btn-ghost btn-sm"
				class:btn-active={$page.url.pathname === '/home'}
			>
				Home
			</a>
			<a
				href="/explore"
				class="btn btn-ghost btn-sm"
				class:btn-active={$page.url.pathname === '/explore'}
			>
				Explore
			</a>
			<a
				href="/group"
				class="btn btn-ghost btn-sm"
				class:btn-active={$page.url.pathname === '/group'}
			>
				Group
			</a>
			<a
				href="/profile"
				class="btn btn-ghost btn-sm"
				class:btn-active={$page.url.pathname === '/profile'}
			>
				Profile
			</a>
		</div>
		<div class="navbar-end">
			<button class="btn btn-ghost btn-sm" onclick={logout}>Logout</button>
		</div>
	</div>
{/if}

{@render children()}
