import React, { createContext, useContext, useEffect, useMemo, useState, useCallback } from 'react';
import { supabase } from '../lib/supabaseClient';
import { apiFetch } from '../lib/apiClient';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [session, setSession] = useState(null);
    const [user, setUser] = useState(null);
    const [selectedPlan, setSelectedPlan] = useState(() => {
        return localStorage.getItem('selectedPlan') || 'free';
    });
    const [loading, setLoading] = useState(true);

    // ── Backend-verified role state (source of truth) ──────────────
    const [userRole, setUserRole] = useState(null);
    const [userProfile, setUserProfile] = useState({
        firstName: '',
        lastName: '',
        bio: '',
        phoneNumber: ''
    });
    const [subscription, setSubscription] = useState({
        tier: 'explorer',
        used: 0,
        remaining: 1,
        resetDate: null
    });
    const [roleLoading, setRoleLoading] = useState(true);
    const [networkError, setNetworkError] = useState(false);

    // ── Fetch role & subscription from Django /api/auth/me/ ────────
    const fetchUserRole = useCallback(async () => {
        try {
            setRoleLoading(true);
            setNetworkError(false);
            const data = await apiFetch('/api/auth/me/');

            setUserRole({
                is_student: data.is_student,
                is_staff: data.is_staff,
                is_superuser: data.is_superuser,
                is_institution_admin: data.is_institution_admin,
            });

            setSubscription({
                tier: data.subscription_tier,
                used: data.prompts_used_in_period,
                remaining: data.prompts_remaining,
                resetDate: data.prompt_period_start
            });

            setUserProfile({
                firstName: data.first_name || '',
                lastName: data.last_name || '',
                bio: data.bio || '',
                phoneNumber: data.phone_number || ''
            });

            // Update local selectedPlan to match backend tier
            setSelectedPlan(data.subscription_tier);
            localStorage.setItem('selectedPlan', data.subscription_tier);

        } catch (err) {
            console.error('[Auth] Failed to fetch user role from backend:', err);
            // Security: DO NOT assume student on network failure
            setUserRole({
                is_student: false,
                is_staff: false,
                is_superuser: false,
                is_institution_admin: false,
            });
            setNetworkError(true);
        } finally {
            setRoleLoading(false);
        }
    }, []);

    useEffect(() => {
        let mounted = true;

        // 1) Load initial session
        supabase.auth.getSession()
            .then(({ data, error }) => {
                if (!mounted) return;
                if (error) console.error('getSession error:', error);
                setSession(data?.session ?? null);
                setUser(data?.session?.user ?? null);
            })
            .catch(err => {
                console.error('Fatal initialization error:', err);
            })
            .finally(() => {
                if (mounted) setLoading(false);
            });

        // 2) Subscribe to auth changes
        const { data: sub } = supabase.auth.onAuthStateChange((_event, newSession) => {
            setSession(newSession);
            setUser(newSession?.user ?? null);
        });

        return () => {
            mounted = false;
            sub?.subscription?.unsubscribe();
        };
    }, []);

    // 3) Fetch backend role whenever session changes (login/logout/refresh)
    useEffect(() => {
        if (session?.access_token) {
            fetchUserRole();
        } else {
            // No session → clear role
            setUserRole(null);
            setRoleLoading(false);
        }
    }, [session, fetchUserRole]);

    // 4) Auto-Logout on Inactivity (60 Minutes)
    useEffect(() => {
        if (!user) return; // Only run if user is logged in

        const TIMEOUT_MS = 60 * 60 * 1000; // 60 minutes
        let lastActivity = Date.now();

        const handleActivity = () => {
            lastActivity = Date.now();
        };

        // Listen for user interactions
        const events = ['mousedown', 'keydown', 'scroll', 'touchstart', 'mousemove'];
        events.forEach(event => window.addEventListener(event, handleActivity));

        // Check for timeout every minute
        const intervalId = setInterval(() => {
            const now = Date.now();
            if (now - lastActivity > TIMEOUT_MS) {
                console.warn(`[Auth] Auto-logout due to inactivity (${TIMEOUT_MS / 60000} mins)`);
                supabase.auth.signOut().then(() => {
                    window.location.href = '/signin?reason=session_expired';
                });
            }
        }, 60000);

        return () => {
            events.forEach(event => window.removeEventListener(event, handleActivity));
            clearInterval(intervalId);
        };
    }, [user]);

    useEffect(() => {
        localStorage.setItem('selectedPlan', selectedPlan);
    }, [selectedPlan]);

    const api = useMemo(() => ({
        session,
        user,
        loading,
        selectedPlan,

        // ── Backend-verified role (source of truth) ──────────────
        userRole,
        subscription, // Tier + usage stats
        userProfile,   // firstName, lastName, bio
        roleLoading,
        networkError,
        fetchUserRole,  // Allow manual refresh after login/upgrade/submission
        refreshAuth: fetchUserRole, // Alias for better readability

        async signup(email, password, options = {}) {
            const { data, error } = await supabase.auth.signUp({
                email,
                password,
                options: {
                    emailRedirectTo: `${window.location.origin}/signin?confirmed=1`,
                    ...options
                }
            });
            if (error) throw error;
            return data;
        },

        async login(email, password) {
            const { data, error } = await supabase.auth.signInWithPassword({ email, password });
            if (error) throw error;
            return data;
        },

        async loginWithGoogle() {
            const redirectTo = `${window.location.origin}/auth/callback`;
            const { data, error } = await supabase.auth.signInWithOAuth({
                provider: 'google',
                options: { redirectTo },
            });
            if (error) throw error;
            return data;
        },

        async resetPassword(email) {
            const { error } = await supabase.auth.resetPasswordForEmail(email, {
                redirectTo: `${window.location.origin}/reset-password`,
            });
            if (error) throw error;
        },

        async updatePassword(newPassword) {
            const { error } = await supabase.auth.updateUser({ password: newPassword });
            if (error) throw error;
        },

        async logout() {
            setUserRole(null);  // Clear role immediately on logout
            const { error } = await supabase.auth.signOut();
            if (error) throw error;
        },

        updateProfile: async (data) => {
            try {
                const response = await apiFetch('/api/auth/me/', {
                    method: 'PUT',
                    body: data
                });

                setUserProfile({
                    firstName: response.first_name,
                    lastName: response.last_name,
                    bio: response.bio,
                    phoneNumber: response.phone_number
                });

                return response;
            } catch (err) {
                console.error('[Auth] Failed to update profile:', err);
                throw err;
            }
        },

        selectPlan(plan) {
            setSelectedPlan(plan);
        }
    }), [session, user, loading, selectedPlan, userRole, subscription, roleLoading, fetchUserRole]);

    return (
        <AuthContext.Provider value={api}>
            {!loading && children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

