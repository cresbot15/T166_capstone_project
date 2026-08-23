<script lang="ts">
	let { value, total, label }: { value: number; total: number; label: string } = $props();

	// TODO: `total` has no real backend source yet — Unit has no enrollment/
	// capacity field. See docs/backlog.md, "Unit enrollment total for StatDonut".
	// Callers currently pass a placeholder constant until that field exists.

	const percent = $derived(total > 0 ? Math.min(1, Math.max(0, value / total)) : 0);

	function polarToCartesian(angleDeg: number) {
		const angleRad = ((angleDeg - 90) * Math.PI) / 180;
		return { x: 50 + 45 * Math.cos(angleRad), y: 50 + 45 * Math.sin(angleRad) };
	}

	const arcPath = $derived.by(() => {
		if (percent <= 0) return '';
		const angle = percent * 360;
		const start = polarToCartesian(0);
		const end = polarToCartesian(angle);
		const largeArcFlag = percent > 0.5 ? 1 : 0;
		return `M50,50 L${start.x},${start.y} A45,45 0 ${largeArcFlag} 1 ${end.x},${end.y} Z`;
	});
</script>

<div class="flex flex-col items-center gap-2">
	<svg width="96" height="96" viewBox="0 0 100 100" aria-hidden="true">
		<circle cx="50" cy="50" r="45" fill="var(--color-base-200)" />
		{#if percent >= 1}
			<circle cx="50" cy="50" r="45" fill="var(--color-accent)" />
		{:else if arcPath}
			<path d={arcPath} fill="var(--color-accent)" />
		{/if}
	</svg>
	<p class="text-center">
		<span class="text-2xl font-extrabold text-primary">{value}</span>
		<span class="block text-sm text-base-content/70">{label}</span>
	</p>
</div>
