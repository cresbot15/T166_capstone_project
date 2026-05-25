<script lang="ts">
	import '../app.css';
	import { token, user } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import type { Snippet } from 'svelte';

	let { children }: { children: Snippet } = $props();

	function logout() {
		token.clear();
		user.set(null);
		goto('/');
	}
</script>

{#if $token}
	<div class="navbar bg-base-100 border-b border-base-300 px-4">
		<div class="navbar-start">
			<a href="/profile" class="font-semibold text-base">TeamUp!</a>
		</div>
		<div class="navbar-center gap-1">
			<a
				href="/profile"
				class="btn btn-ghost btn-sm"
				class:btn-active={$page.url.pathname === '/profile'}
			>
				Profile
			</a>
			<a
				href="/group"
				class="btn btn-ghost btn-sm"
				class:btn-active={$page.url.pathname === '/group'}
			>
				Group
			</a>
		</div>
		<div class="navbar-end">
			<button class="btn btn-ghost btn-sm" onclick={logout}>Logout</button>
		</div>
	</div>
{/if}

{@render children()}
