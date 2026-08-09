import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import type { UserResponse, UnitResponse } from '$lib/api';

function createTokenStore() {
	const initial = browser ? localStorage.getItem('token') : null;
	const { subscribe, set } = writable<string | null>(initial);
	return {
		subscribe,
		set(val: string | null) {
			if (browser) {
				if (val) localStorage.setItem('token', val);
				else localStorage.removeItem('token');
			}
			set(val);
		},
		clear() {
			this.set(null);
		}
	};
}

function createActiveUnitStore() {
	const raw = browser ? localStorage.getItem('activeUnit') : null;
	const initial: UnitResponse | null = raw ? JSON.parse(raw) : null;
	const { subscribe, set } = writable<UnitResponse | null>(initial);
	return {
		subscribe,
		set(val: UnitResponse | null) {
			if (browser) {
				if (val) localStorage.setItem('activeUnit', JSON.stringify(val));
				else localStorage.removeItem('activeUnit');
			}
			set(val);
		},
		clear() {
			this.set(null);
		}
	};
}

export const token = createTokenStore();
export const user = writable<UserResponse | null>(null);
export const activeUnit = createActiveUnitStore();
