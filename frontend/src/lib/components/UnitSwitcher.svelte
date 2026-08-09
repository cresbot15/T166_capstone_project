<script lang="ts">
	import type { UnitResponse } from '$lib/api';

	let {
		units,
		activeUnitId,
		onSwitch
	}: {
		units: UnitResponse[];
		activeUnitId: number | null;
		onSwitch: (unit: UnitResponse) => void;
	} = $props();

	const activeUnit = $derived(units.find((u) => u.id === activeUnitId) ?? null);
</script>

<div class="dropdown">
	<div tabindex="0" role="button" class="btn btn-ghost btn-sm">
		{activeUnit ? (activeUnit.name ?? activeUnit.code) : 'Select unit'} ▾
	</div>
	<ul class="dropdown-content menu bg-base-100 text-base-content rounded-box shadow-sm z-10 w-52 p-2">
		{#each units as unit}
			<li>
				<button class:menu-active={unit.id === activeUnitId} onclick={() => onSwitch(unit)}>
					{unit.name ?? unit.code}
				</button>
			</li>
		{/each}
	</ul>
</div>
