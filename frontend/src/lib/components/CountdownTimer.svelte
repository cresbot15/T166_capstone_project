<script lang="ts">
	import { onMount } from 'svelte';

	let { targetDate }: { targetDate: string } = $props();

	let days = $state(0);
	let hours = $state(0);
	let minutes = $state(0);

	function update() {
		const diff = Math.max(0, new Date(targetDate).getTime() - Date.now());
		const totalMinutes = Math.floor(diff / 60000);
		days = Math.floor(totalMinutes / (60 * 24));
		hours = Math.floor((totalMinutes % (60 * 24)) / 60);
		minutes = totalMinutes % 60;
	}

	onMount(() => {
		update();
		const interval = setInterval(update, 60000);
		return () => clearInterval(interval);
	});

	const units = $derived([
		[days, 'days'],
		[hours, 'hours'],
		[minutes, 'minutes']
	] as const);
</script>

<div class="flex gap-3 justify-center">
	{#each units as [value, label]}
		<div class="flex flex-col items-center">
			<div
				class="bg-primary text-primary-content rounded-lg w-12 h-12 flex items-center justify-center text-lg font-bold"
			>
				{String(value).padStart(2, '0')}
			</div>
			<span class="text-xs text-base-content/60 mt-1">{label}</span>
		</div>
	{/each}
</div>
