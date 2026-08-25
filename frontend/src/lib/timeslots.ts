export const DAYS = [
	'monday',
	'tuesday',
	'wednesday',
	'thursday',
	'friday',
	'saturday',
	'sunday'
] as const;

export function parseSlot(slot: string): { day: string; hour: number } {
	return { day: slot.slice(0, -2), hour: parseInt(slot.slice(-2), 10) };
}

export function slotId(day: string, hour: number): string {
	return `${day}${hour.toString().padStart(2, '0')}`;
}

export function formatHour(hour: number): string {
	const period = hour < 12 ? 'am' : 'pm';
	const displayHour = hour % 12 === 0 ? 12 : hour % 12;
	return `${displayHour}${period}`;
}

export function formatSlot(slot: string): string {
	const { day, hour } = parseSlot(slot);
	const dayLabel = day.charAt(0).toUpperCase() + day.slice(1);
	return `${dayLabel} ${formatHour(hour)}`;
}

// The offered range for a newly-created unit, until unit owners can configure
// their own hours/days. Weekdays 9am-6pm covers realistic meeting times
// without the full 24-hour, 7-day grid's needless complexity.
const DEFAULT_DAYS = DAYS.filter((day) => day !== 'saturday' && day !== 'sunday');
const DEFAULT_START_HOUR = 9;
const DEFAULT_END_HOUR = 17;

export function defaultTimeSlots(): string[] {
	const slots: string[] = [];
	for (const day of DEFAULT_DAYS) {
		for (let hour = DEFAULT_START_HOUR; hour <= DEFAULT_END_HOUR; hour++) {
			slots.push(slotId(day, hour));
		}
	}
	return slots;
}
