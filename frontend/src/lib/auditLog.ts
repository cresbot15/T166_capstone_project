import type { UnitEventResponse } from '$lib/api';

export function eventLabel(event: UnitEventResponse): string {
	const actor = event.actor_name ?? 'Someone';
	const subject = event.subject_name;
	switch (event.event_type) {
		case 'unit.member_joined':
			return `${actor} joined the unit`;
		case 'unit.member_left':
			return `${actor} left the unit`;
		case 'unit.role_changed':
			return `${actor} changed ${subject ?? 'a member'}'s role`;
		case 'group.created':
			return `${actor} created a group`;
		case 'group.deleted':
			return `${actor} deleted a group`;
		case 'group.member_joined':
			return `${actor} joined a group`;
		case 'group.member_left':
			return `${actor} left a group`;
		case 'group.member_removed':
			return `${actor} removed ${subject ?? 'a member'} from a group`;
		case 'group.status_changed':
			return `A group's status changed`;
		default:
			return event.event_type;
	}
}
