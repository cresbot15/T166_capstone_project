<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { token, user, activeUnit, unitRole } from '$lib/stores';
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

		const current = get(activeUnit);
		if (current) {
			const fresh = myUnits.find((u) => u.id === current.id);
			if (fresh) activeUnit.set(fresh);
		}
	});

	function logout() {
		token.clear();
		user.set(null);
		activeUnit.clear();
		goto('/');
	}

	async function refreshUnitRole(unitId: number | null) {
		if (unitId === null) {
			unitRole.set(null);
			return;
		}
		try {
			const profile = await api.getMyUnitProfile(unitId);
			unitRole.set(profile.role);
		} catch {
			unitRole.set(null);
		}
	}

	function switchUnit(unit: UnitResponse) {
		activeUnit.set(unit);
		goto('/home');
	}

	// Refetches whenever the active unit changes for any reason — initial load,
	// a fresh login setting it for the first time, or switching units — rather
	// than only on this layout's own mount, which a client-side login/switch
	// never re-triggers.
	$effect(() => {
		refreshUnitRole($activeUnit?.id ?? null);
	});

	const isUnitStaff = $derived($unitRole === 'owner' || $unitRole === 'administrator');
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
			{#if isUnitStaff}
				<a
					href="/admin/members"
					class="btn btn-ghost btn-sm"
					class:btn-active={$page.url.pathname === '/admin/members'}
				>
					Manage Members
				</a>
				<a
					href="/admin/groups"
					class="btn btn-ghost btn-sm"
					class:btn-active={$page.url.pathname === '/admin/groups'}
				>
					Manage Groups
				</a>
				<a
					href="/admin/audit-log"
					class="btn btn-ghost btn-sm"
					class:btn-active={$page.url.pathname === '/admin/audit-log'}
				>
					Audit Log
				</a>
			{/if}
		</div>
		<div class="navbar-end">
			<button class="btn btn-ghost btn-sm" onclick={logout}>Logout</button>
		</div>
	</div>
{/if}

{@render children()}
