/**
 * Minimal API client that always attaches the current Supabase access token.
 * - Uses Authorization: Bearer <access_token> (verified by backend apps/users/auth/supabase.py)
 * - Always reads getSession() so token refresh is respected.
 * - VITE_API_BASE_URL is baked in at build time (frontend/.env.production for cPanel builds).
 *
 * On a non-2xx response it throws an Error whose:
 *   message = backend `detail` || `message` || `error` || "API Error <status>"
 *   status  = HTTP status code (e.g. 403)
 *   data    = parsed JSON body, if any (e.g. { error: 'PROMPT_LIMIT_REACHED', ... })
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
        let errorData = null;
        try {
            errorData = JSON.parse(text);
            errorMsg = errorData.detail || errorData.message || errorData.error || errorMsg;
        } catch {
            errorMsg = text || errorMsg;
        }
        const err = new Error(errorMsg);
        err.status = res.status;
        err.data = errorData;
        throw err;
    }

    const contentType = res.headers.get('content-type') || '';
    return contentType.includes('application/json') ? res.json() : res.text();
}
