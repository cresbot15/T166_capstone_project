<script lang="ts">
	import { DAYS, PERIODS } from '$lib/timeslots';

	let {
		selected,
		readonly = false,
		onToggle
	}: { selected: Set<string>; readonly?: boolean; onToggle?: (slot: string) => void } = $props();

	function dayLabel(day: string): string {
		return day.charAt(0).toUpperCase() + day.slice(1);
	}
</script>

<div class="overflow-x-auto">
	<table class="table table-sm">
		<thead>
			<tr>
				<th></th>
				{#each PERIODS as period}
					<th class="text-center font-medium text-base-content/60">{period}</th>
				{/each}
			</tr>
		</thead>
		<tbody>
			{#each DAYS as day}
				<tr>
					<td class="text-sm text-base-content/70 pr-4">{dayLabel(day)}</td>
					{#each PERIODS as period}
						{@const slot = `${day}${period}`}
						<td class="text-center">
							{#if readonly}
								<span
									class="text-sm {selected.has(slot)
										? 'text-primary font-semibold'
										: 'text-base-content/20'}"
								>
									{selected.has(slot) ? '✓' : '·'}
								</span>
							{:else}
								<input
									type="checkbox"
									class="checkbox checkbox-sm checkbox-primary"
									checked={selected.has(slot)}
									onchange={() => onToggle?.(slot)}
								/>
							{/if}
						</td>
					{/each}
				</tr>
			{/each}
		</tbody>
	</table>
</div>
