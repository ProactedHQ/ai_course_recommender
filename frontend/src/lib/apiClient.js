/**
 * Minimal API client that always attaches the current Supabase access token.
 * - Uses Authorization: Bearer <access_token>
 * - Always reads getSession() so token refresh is respected.
 */
import { supabase } from './supabaseClient';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function apiFetch(path, { method = 'GET', headers = {}, body } = {}) {
    const { data, error } = await supabase.auth.getSession();
    if (error) throw error;

    const token = data?.session?.access_token;

    const res = await fetch(`${API_BASE}${path}`, {
        method,
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...headers,
        },
        body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
        const text = await res.text();
        let errorMsg = `API Error ${res.status}`;
        try {
            const json = JSON.parse(text);
            errorMsg = json.detail || json.message || errorMsg;
        } catch {
            errorMsg = text || errorMsg;
        }
        throw new Error(errorMsg);
    }

    const contentType = res.headers.get('content-type') || '';
    return contentType.includes('application/json') ? res.json() : res.text();
}
