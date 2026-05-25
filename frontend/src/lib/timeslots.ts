export const DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'] as const;
export const PERIODS = ['Morning', 'Afternoon', 'Evening'] as const;

export function formatSlot(slot: string): string {
	return slot.replace(/([A-Z])/g, ' $1').replace(/^./, (s) => s.toUpperCase());
}
