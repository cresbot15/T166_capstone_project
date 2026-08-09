<script module lang="ts">
	export type Status = 'complete' | 'incomplete' | 'pending';
</script>

<script lang="ts">
	let { status, label }: { status: Status; label?: string } = $props();

	const badgeClass: Record<Status, string> = {
		complete: 'badge-success',
		pending: 'badge-warning',
		incomplete: 'badge-error'
	};

	const defaultLabel: Record<Status, string> = {
		complete: 'Complete',
		pending: 'Pending',
		incomplete: 'Incomplete'
	};
</script>

<span class="badge {badgeClass[status]} font-semibold">
	{label ?? defaultLabel[status]}
</span>
