<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { token, user, activeUnit, unitRole } from '$lib/stores';
	import { api } from '$lib/api';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import SectionCard from '$lib/components/SectionCard.svelte';
	import CountdownTimer from '$lib/components/CountdownTimer.svelte';
	import StatDonut from '$lib/components/StatDonut.svelte';

	let readyCount = $state(0);
	let provisionalCount = $state(0);
	let ungroupedCount = $state(0);

	const isUnitStaff = $derived($unitRole === 'owner' || $unitRole === 'administrator');

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
			const [members, groups] = await Promise.all([
				api.getUnitMembers($activeUnit.id),
				api.getGroups($activeUnit.id)
			]);
			const students = members.filter((m) => m.role === 'student');
			const statusByUserId = new Map<number, 'pending' | 'provisional'>();
			for (const g of groups) {
				for (const m of g.members) statusByUserId.set(m.id, g.status);
			}
			readyCount = students.filter((s) => statusByUserId.get(s.user_id) === 'pending').length;
			provisionalCount = students.filter(
				(s) => statusByUserId.get(s.user_id) === 'provisional'
			).length;
			ungroupedCount = students.length - readyCount - provisionalCount;
		} catch {
			// Leave the stats at 0 — the rest of the page is still usable
		}
	});
</script>

{#if $activeUnit}
	<PageHeader
		title={`Welcome, ${$user?.first_name ?? ''}!`}
		subtitle={$activeUnit.name ?? $activeUnit.code}
	/>

	<div class="max-w-3xl mx-auto px-4 py-8 grid gap-4 md:grid-cols-2">
		<div class="flex flex-col gap-3">
			{#if isUnitStaff}
				<a href="/admin/members" class="btn btn-primary btn-block">Manage Members</a>
				<a href="/admin/groups" class="btn btn-outline btn-block">Manage Groups</a>
			{:else}
				<a href="/group" class="btn btn-primary btn-block">Create a Group</a>
				<a href="/explore" class="btn btn-outline btn-block">Explore Students & Groups</a>
			{/if}
		</div>

		<SectionCard>
			<StatDonut
				centerLabel="students in this unit"
				segments={[
					{ value: readyCount, color: 'var(--color-success)', label: 'In a ready group' },
					{ value: provisionalCount, color: 'var(--color-warning)', label: 'In a provisional group' },
					{ value: ungroupedCount, color: 'var(--color-base-300)', label: 'Not in a group' }
				]}
			/>
		</SectionCard>

		<div class="md:col-span-2">
			<SectionCard title="Initial groupings are due">
				{#if $activeUnit.formation_end_date}
					<CountdownTimer targetDate={$activeUnit.formation_end_date} />
				{:else}
					<p class="text-sm text-base-content/60">
						No formation deadline set for this unit.
					</p>
				{/if}
			</SectionCard>
		</div>
	</div>
{/if}
