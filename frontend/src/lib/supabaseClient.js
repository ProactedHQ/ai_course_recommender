/**
 * Supabase client singleton for the frontend.
 * - Uses the public client key (anon / publishable key) - safe for the browser, never a secret.
 * - Handles session persistence + token refresh automatically in SPAs.
 *
 * Which project:
 *   production build (`npm run build`)  -> frontend/.env.production  -> production project
 *   local dev (`npm run dev`)           -> frontend/.env.development(.local) -> development project
 * Local development refuses the production project, so developers never sign in to (or create)
 * real production accounts by accident.
 */
import { createClient } from '@supabase/supabase-js';

// Public project id of the production Supabase project (already in the production bundle).
const PRODUCTION_SUPABASE_REF = 'zuoujlipkmoqxrwcrdij';

let supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
let supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (import.meta.env.MODE === 'development' && supabaseUrl?.includes(PRODUCTION_SUPABASE_REF)) {
  console.error(
    'Local development must not use the PRODUCTION Supabase project. Put the development project ' +
    'URL and public key in frontend/.env.development.local (see docs/PAYMENTS.md, "Development login").'
  );
  supabaseUrl = undefined;
  supabaseAnonKey = undefined;
}

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
