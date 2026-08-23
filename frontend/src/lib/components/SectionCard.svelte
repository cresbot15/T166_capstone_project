<script lang="ts">
	import type { Snippet } from 'svelte';

	let { title, children }: { title?: string; children: Snippet } = $props();
</script>

<div class="card bg-base-100 shadow-sm rounded-2xl">
	<div class="card-body">
		{#if title}
			<h2 class="font-bold text-lg mb-2">{title}</h2>
		{/if}
		{@render children()}
	</div>
</div>
