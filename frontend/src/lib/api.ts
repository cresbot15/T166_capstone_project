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
	is_new_student: boolean;
	delivery_mode: string | null;
	skills: string | null;
	time_preferences: string[];
	group_id: number | null;
}

export interface TokenResponse {
	access_token: string;
	token_type: string;
}

export interface GroupResponse {
	id: number;
	preference_code: string | null;
	members: UserResponse[];
	status: 'valid' | 'provisional';
	common_time_slots: string[];
}

export interface GroupJoinResponse {
	valid: boolean;
	reason?: string;
	group: GroupResponse;  // only present when valid is true
}

export const api = {
	register: (data: Record<string, unknown>) => req<UserResponse>('POST', '/auth/register', data),
	login: (email: string, password: string) =>
		req<TokenResponse>('POST', '/auth/login', { email, password }),
	getMe: () => req<UserResponse>('GET', '/users/me'),
	updateMe: (data: Record<string, unknown>) => req<UserResponse>('PUT', '/users/me', data),
	joinGroup: (code: string) =>
		req<GroupJoinResponse>('POST', '/groups/join', { preference_code: code }),
	createGroup: (code?: string) =>
		req<GroupResponse>('POST', '/groups/create', { preference_code: code }),
	getMyGroup: () => req<GroupResponse>('GET', '/groups/my-group'),
	getRecommendedTimes: () => req<string[]>('GET', '/groups/recommended-times'),
	leaveGroup: () => req<null>('DELETE', '/groups/leave')
};
