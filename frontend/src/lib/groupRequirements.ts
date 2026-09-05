import type { UnitResponse } from '$lib/api';

export const REQUIREMENT_LABELS: Record<string, (unit: UnitResponse) => string> = {
	min_group_size: (unit) => `Needs at least ${unit.min_group_size} members.`,
	common_time_slot: () => 'No time slot is shared by all members yet.',
	max_new_students: (unit) => `Too many new students for this group (unit max: ${unit.max_new_students}).`
};
