<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		title,
		subtitle,
		actions
	}: { title: string; subtitle?: string; actions?: Snippet } = $props();
</script>

<div class="bg-primary text-primary-content rounded-b-2xl px-6 py-5 flex items-center justify-between gap-4">
	<div>
		<h1 class="text-2xl font-extrabold tracking-tight">{title}</h1>
		{#if subtitle}
			<p class="text-primary-content/70 text-sm mt-1">{subtitle}</p>
		{/if}
	</div>
	{#if actions}
		<div class="flex items-center gap-2">
			{@render actions()}
		</div>
	{/if}
</div>
