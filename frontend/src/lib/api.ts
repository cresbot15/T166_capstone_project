const BASE = '/api';

function authHeaders(): Record<string, string> {
	const token = typeof localStorage !== 'undefined' ? localStorage.getItem('token') : null;
	return token ? { Authorization: `Bearer ${token}` } : {};
}

async function req<T>(method: string, path: string, body?: unknown): Promise<T> {
	const headers: Record<string, string> = {
		'Content-Type': 'application/json',
		...authHeaders()
	};
	const res = await fetch(`${BASE}${path}`, {
		method,
		headers,
		body: body !== undefined ? JSON.stringify(body) : undefined
	});
	if (res.status === 204) return null as T;
	const data = await res.json();
	if (!res.ok) throw new Error(data.detail || 'Request failed');
	return data as T;
}

export interface UserResponse {
	id: number;
	first_name: string;
	last_name: string;
	email: string;
	role: string;
}

export interface TokenResponse {
	access_token: string;
	token_type: string;
}

export interface UnitResponse {
	id: number;
	code: string;
	name: string | null;
	min_group_size: number;
	max_group_size: number;
	max_new_students: number | null;
	time_slots: string[];
}

export interface UnitMeResponse {
	unit_id: number;
	role: string;
	is_new_student: boolean;
	delivery_mode: string | null;
	skills: string | null;
	time_preferences: string[];
}

export interface UnitMembershipResponse {
	user_id: number;
	unit_id: number;
	role: string;
}

export interface UnitMemberResponse {
	user_id: number;
	first_name: string;
	last_name: string;
	email: string;
	role: string;
	is_new_student: boolean;
	delivery_mode: string | null;
	skills: string | null;
	time_preferences: string[];
}

export interface GroupResponse {
	id: number;
	preference_code: string | null;
	unit_id: number;
	creator_user_id: number | null;
	is_public: boolean;
	members: UserResponse[];
	status: 'pending' | 'provisional';
	unmet_requirements: string[];
	common_time_slots: string[];
}

export interface GroupJoinResponse {
	valid: boolean;
	reason?: string;
	group?: GroupResponse;
}

export interface UnitEventResponse {
	id: number;
	unit_id: number;
	event_type: string;
	actor_user_id: number | null;
	actor_name: string | null;
	subject_user_id: number | null;
	subject_name: string | null;
	group_id: number | null;
	detail: Record<string, unknown> | null;
	created_at: string;
}

export const api = {
	register: (data: {
		first_name: string;
		last_name: string;
		email: string;
		password: string;
		role?: 'student' | 'unit_coordinator';
	}) => req<UserResponse>('POST', '/auth/register', data),
	login: (email: string, password: string) =>
		req<TokenResponse>('POST', '/auth/login', { email, password }),
	getMe: () => req<UserResponse>('GET', '/users/me'),

	getMyUnits: () => req<UnitResponse[]>('GET', '/units/me'),
	joinUnit: (code: string) => req<UnitResponse>('POST', '/units/join', { code }),
	createUnit: (name?: string, timeSlots?: string[]) =>
		req<UnitResponse>('POST', '/units/create', { name, time_slots: timeSlots }),
	getMyUnitProfile: (unitId: number) => req<UnitMeResponse>('GET', `/units/${unitId}/me`),
	updateMyUnitProfile: (
		unitId: number,
		data: Partial<{
			is_new_student: boolean;
			delivery_mode: string;
			skills: string;
			time_preferences: string[];
		}>
	) => req<UnitMeResponse>('PATCH', `/units/${unitId}/me`, data),
	getUnitMembers: (unitId: number) => req<UnitMemberResponse[]>('GET', `/units/${unitId}/members`),
	setMemberRole: (unitId: number, userId: number, role: 'administrator' | 'student') =>
		req<UnitMembershipResponse>('PATCH', `/units/${unitId}/members/${userId}`, { role }),
	getTimeSlots: () => req<string[]>('GET', '/time-slots'),
	exportUnitStudents: async (unitId: number): Promise<void> => {
		const res = await fetch(`${BASE}/units/${unitId}/export`, { headers: authHeaders() });
		if (!res.ok) {
			const data = await res.json().catch(() => ({}));
			throw new Error(data.detail || 'Export failed');
		}
		const blob = await res.blob();
		const disposition = res.headers.get('Content-Disposition') ?? '';
		const match = disposition.match(/filename="?([^"]+)"?/);
		const filename = match?.[1] ?? 'export.csv';
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = filename;
		a.click();
		URL.revokeObjectURL(url);
	},

	createGroup: (unitId: number, isPublic: boolean) =>
		req<GroupResponse>('POST', '/groups/create', { unit_id: unitId, is_public: isPublic }),
	joinGroup: (preferenceCode: string) =>
		req<GroupJoinResponse>('POST', '/groups/join', { preference_code: preferenceCode }),
	getGroups: (unitId: number) => req<GroupResponse[]>('GET', `/groups/${unitId}`),
	getMyGroups: () => req<GroupResponse[]>('GET', '/groups/my-groups'),
	getRecommendedTimes: (unitId: number, groupId: number) =>
		req<string[]>('GET', `/groups/${unitId}/${groupId}/recommended-times`),
	leaveGroup: (unitId: number, groupId: number) =>
		req<null>('DELETE', `/groups/${unitId}/${groupId}/leave`),
	removeGroupMember: (unitId: number, groupId: number, userId: number) =>
		req<null>('DELETE', `/groups/${unitId}/${groupId}/members/${userId}`),
	getUnitEvents: (
		unitId: number,
		params?: { groupId?: number; userId?: number; limit?: number; offset?: number }
	) => {
		const qs = new URLSearchParams();
		if (params?.limit !== undefined) qs.set('limit', String(params.limit));
		if (params?.offset !== undefined) qs.set('offset', String(params.offset));
		const query = qs.toString() ? `?${qs.toString()}` : '';
		if (params?.groupId !== undefined) {
			return req<UnitEventResponse[]>('GET', `/events/${unitId}/group/${params.groupId}${query}`);
		}
		if (params?.userId !== undefined) {
			return req<UnitEventResponse[]>('GET', `/events/${unitId}/user/${params.userId}${query}`);
		}
		return req<UnitEventResponse[]>('GET', `/events/${unitId}${query}`);
	}
};
