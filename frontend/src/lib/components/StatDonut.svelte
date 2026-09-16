<script lang="ts">
	interface Segment {
		value: number;
		color: string;
		label: string;
	}

	let { segments, centerLabel }: { segments: Segment[]; centerLabel: string } = $props();

	const total = $derived(segments.reduce((sum, s) => sum + s.value, 0));

	function polarToCartesian(angleDeg: number) {
		const angleRad = ((angleDeg - 90) * Math.PI) / 180;
		return { x: 50 + 45 * Math.cos(angleRad), y: 50 + 45 * Math.sin(angleRad) };
	}

	// Cumulative angle per slice, in the caller's fixed order — never resorted
	// by size, so a category's color/position stays stable as counts change.
	const slices = $derived.by(() => {
		let angleSoFar = 0;
		return segments
			.filter((s) => s.value > 0)
			.map((s) => {
				const share = total > 0 ? s.value / total : 0;
				const startAngle = angleSoFar;
				const endAngle = angleSoFar + share * 360;
				angleSoFar = endAngle;
				return { ...s, startAngle, endAngle, share };
			});
	});

	function slicePath(startAngle: number, endAngle: number): string {
		const start = polarToCartesian(startAngle);
		const end = polarToCartesian(endAngle);
		const largeArcFlag = endAngle - startAngle > 180 ? 1 : 0;
		return `M50,50 L${start.x},${start.y} A45,45 0 ${largeArcFlag} 1 ${end.x},${end.y} Z`;
	}
</script>

<div class="flex flex-col items-center gap-3">
	<svg width="96" height="96" viewBox="0 0 100 100" aria-hidden="true">
		{#if total === 0}
			<circle cx="50" cy="50" r="45" fill="var(--color-base-300)" />
		{:else if slices.length === 1}
			<circle cx="50" cy="50" r="45" fill={slices[0].color} />
		{:else}
			{#each slices as slice}
				<path
					d={slicePath(slice.startAngle, slice.endAngle)}
					fill={slice.color}
					stroke="var(--color-base-100)"
					stroke-width="2"
				/>
			{/each}
		{/if}
	</svg>

	<p class="text-center">
		<span class="text-2xl font-extrabold text-primary">{total}</span>
		<span class="block text-sm text-base-content/70">{centerLabel}</span>
	</p>

	<ul class="flex flex-col gap-1 w-full">
		{#each segments as s}
			<li class="flex items-center gap-2 text-sm">
				<span class="w-2.5 h-2.5 rounded-full flex-shrink-0" style="background-color: {s.color}"
				></span>
				<span class="text-base-content/70 flex-1">{s.label}</span>
				<span class="font-semibold">{s.value}</span>
			</li>
		{/each}
	</ul>
</div>
