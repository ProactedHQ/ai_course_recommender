/**
 * Supabase client singleton for the frontend.
 * - Uses anon key (safe for browser).
 * - Handles session persistence + token refresh automatically in SPAs.
 */
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn('VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY is missing. Auth will fail.');
}

// Custom storage proxy to handle "Remember Me" logic (localStorage vs sessionStorage)
const customStorage = {
  getItem: (key) => {
    try {
      const rememberMe = localStorage.getItem('supabase.remember_me') === 'true';
      return rememberMe ? localStorage.getItem(key) : sessionStorage.getItem(key);
    } catch {
      return null;
    }
  },
  setItem: (key, value) => {
    try {
      const rememberMe = localStorage.getItem('supabase.remember_me') === 'true';
      if (rememberMe) {
        localStorage.setItem(key, value);
      } else {
        sessionStorage.setItem(key, value);
      }
    } catch {
      // Fallback or ignore
    }
  },
  removeItem: (key) => {
    try {
      localStorage.removeItem(key);
      sessionStorage.removeItem(key);
    } catch {
      // Ignore
    }
  },
};

export const supabase = createClient(supabaseUrl || 'https://placeholder.supabase.co', supabaseAnonKey || 'placeholder', {
  auth: {
    storage: customStorage,
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
});
