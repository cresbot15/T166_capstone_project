import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import type { UserResponse } from '$lib/api';

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

export const token = createTokenStore();
export const user = writable<UserResponse | null>(null);
