/**
 * AuthCallback page.
 * - Supabase detects session in URL and stores it.
 * - Fetches backend-verified role, then redirects based on role.
 */
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../../lib/supabaseClient';
import { apiFetch } from '../../lib/apiClient';

export default function AuthCallback() {
    const navigate = useNavigate();

    useEffect(() => {
        (async () => {
            const { data } = await supabase.auth.getSession();
            if (data?.session) {
                try {
                    // Fetch backend-verified role (source of truth)
                    const roleData = await apiFetch('/api/auth/me/');
                    const isStaff = roleData.is_staff === true && roleData.is_student === false;

                    if (isStaff) {
                        navigate('/admin/dashboard', { replace: true });
                    } else {
                        navigate('/app', { replace: true });
                    }
                } catch (err) {
                    console.error('[AuthCallback] Role fetch failed, defaulting to /app:', err);
                    navigate('/app', { replace: true });
                }
            } else {
                navigate('/signin', { replace: true });
            }
        })();
    }, [navigate]);

    return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', fontFamily: 'Inter, sans-serif' }}>
            <div style={{ textAlign: 'center' }}>
                <h2 style={{ color: '#0A1926', marginBottom: '16px' }}>Authenticating...</h2>
                <p style={{ color: '#64748b' }}>Completing your secure sign-in, please wait.</p>
            </div>
        </div>
    );
}

