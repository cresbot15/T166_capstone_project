const BASE = 'http://localhost:8000';

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
}

export interface TokenResponse {
	access_token: string;
	token_type: string;
}

export interface UnitResponse {
	id: number;
	code: string;
	name: string | null;
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

export interface GroupResponse {
	id: number;
	preference_code: string | null;
	unit_id: number;
	creator_user_id: number | null;
	is_public: boolean;
	members: UserResponse[];
	status: 'valid' | 'provisional';
	common_time_slots: string[];
}

export interface GroupJoinResponse {
	valid: boolean;
	reason?: string;
	group?: GroupResponse;
}

export const api = {
	register: (data: { first_name: string; last_name: string; email: string; password: string }) =>
		req<UserResponse>('POST', '/auth/register', data),
	login: (email: string, password: string) =>
		req<TokenResponse>('POST', '/auth/login', { email, password }),
	getMe: () => req<UserResponse>('GET', '/users/me'),

	getMyUnits: () => req<UnitResponse[]>('GET', '/units/me'),
	joinUnit: (code: string) => req<UnitResponse>('POST', '/units/join', { code }),
	createUnit: (name?: string) => req<UnitResponse>('POST', '/units/create', { name }),
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
	setMemberRole: (unitId: number, email: string, role: 'administrator' | 'student') =>
		req<UnitMembershipResponse>(
			'PATCH',
			`/units/${unitId}/members/${encodeURIComponent(email)}`,
			{ role }
		),

	createGroup: (unitId: number, isPublic: boolean) =>
		req<GroupResponse>('POST', '/groups/create', { unit_id: unitId, is_public: isPublic }),
	joinGroup: (preferenceCode: string) =>
		req<GroupJoinResponse>('POST', '/groups/join', { preference_code: preferenceCode }),
	getGroups: (unitId: number) => req<GroupResponse[]>('GET', `/groups/${unitId}`),
	getMyGroups: () => req<GroupResponse[]>('GET', '/groups/my-groups'),
	getRecommendedTimes: (unitId: number, groupId: number) =>
		req<string[]>('GET', `/groups/${unitId}/${groupId}/recommended-times`),
	leaveGroup: (unitId: number, groupId: number) =>
		req<null>('DELETE', `/groups/${unitId}/${groupId}/leave`)
};
