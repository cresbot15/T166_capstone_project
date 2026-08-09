<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { token, user, activeUnit } from '$lib/stores';
	import { mockStudents } from '$lib/mockStudents';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import SectionCard from '$lib/components/SectionCard.svelte';
	import CountdownTimer from '$lib/components/CountdownTimer.svelte';
	import StatDonut from '$lib/components/StatDonut.svelte';

	// Placeholder due date — no due_date field exists on Unit yet (see design
	// spec Non-goals). Replace with a real per-unit value if that field is added.
	const GROUPINGS_DUE = '2026-09-15T00:00:00';

	// TODO: placeholder enrollment total — Unit has no capacity/enrollment
	// field yet (see docs/backlog.md, "Unit enrollment total for StatDonut").
	// Replace with a real per-unit value once that field exists.
	const EXPECTED_ENROLLMENT = 200;

	onMount(() => {
		if (!$token) {
			goto('/');
			return;
		}
		if (!$activeUnit) {
			goto('/onboarding/unit');
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
			<a href="/group" class="btn btn-primary btn-block">Create a Group</a>
			<a href="/explore" class="btn btn-outline btn-block">Explore Students & Groups</a>
		</div>

		<SectionCard>
			<StatDonut
				value={mockStudents.length}
				total={EXPECTED_ENROLLMENT}
				label="students have registered in TeamUp!"
			/>
		</SectionCard>

		<div class="md:col-span-2">
			<SectionCard title="Initial groupings are due">
				<CountdownTimer targetDate={GROUPINGS_DUE} />
			</SectionCard>
		</div>
	</div>
{/if}
