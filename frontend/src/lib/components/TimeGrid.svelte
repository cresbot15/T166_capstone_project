<script lang="ts">
	import { DAYS, parseSlot, slotId, formatHour, formatSlot } from '$lib/timeslots';

	let {
		slots,
		selected,
		readonly = false,
		onToggle
	}: {
		slots: string[];
		selected: Set<string>;
		readonly?: boolean;
		onToggle?: (slot: string) => void;
	} = $props();

	const hoursByDay = $derived.by(() => {
		const map = new Map<string, Set<number>>();
		for (const slot of slots) {
			const { day, hour } = parseSlot(slot);
			if (!map.has(day)) map.set(day, new Set());
			map.get(day)!.add(hour);
		}
		return map;
	});

	const days = $derived(DAYS.filter((day) => hoursByDay.has(day)));

	// Only the hours actually offered get a column — a unit offering a narrow
	// range (e.g. 9am-6pm) shouldn't render a full 24-wide grid padded with
	// unusable blank columns either side.
	const hours = $derived.by(() => {
		const set = new Set<number>();
		for (const slot of slots) set.add(parseSlot(slot).hour);
		return Array.from(set).sort((a, b) => a - b);
	});

	function dayLabel(day: string): string {
		return day.charAt(0).toUpperCase() + day.slice(1);
	}
</script>

<div class="overflow-x-auto">
	<div
		class="inline-grid gap-0.5"
		style="grid-template-columns: auto repeat({hours.length}, 1.25rem);"
	>
		<div></div>
		{#each hours as hour}
			<div class="text-[10px] font-normal text-base-content/50 text-center">
				{hour % 3 === 0 ? formatHour(hour) : ''}
			</div>
		{/each}

		{#each days as day}
			<div class="text-xs text-base-content/70 pr-2 whitespace-nowrap self-center">
				{dayLabel(day)}
			</div>
			{#each hours as hour}
				{@const offered = hoursByDay.get(day)?.has(hour) ?? false}
				{@const slot = slotId(day, hour)}
				{#if !offered}
					<div class="w-5 h-5"></div>
				{:else if readonly}
					<div
						class="w-5 h-5 rounded {selected.has(slot) ? 'bg-accent' : 'bg-base-200'}"
						title={formatSlot(slot)}
					></div>
				{:else}
					<button
						type="button"
						class="w-5 h-5 rounded transition-colors {selected.has(slot)
							? 'bg-accent'
							: 'bg-base-200 hover:bg-base-300'}"
						aria-pressed={selected.has(slot)}
						title={formatSlot(slot)}
						onclick={() => onToggle?.(slot)}
					></button>
				{/if}
			{/each}
		{/each}
	</div>
</div>
