import { Navigate, useLocation } from 'react-router-dom';
import { Fingerprint } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const ProtectedRoute = ({ children }) => {
    const { user, userRole, roleLoading, networkError } = useAuth();
    const location = useLocation();

    // 1) Not authenticated at all → sign in
    if (!user) {
        return <Navigate to={`/signin?returnTo=${location.pathname}`} replace />;
    }

    // 2) Network error → always show error (user needs to act)
    if (networkError) {
        return (
            <div className="verification-container">
                <div className="verification-spinner-wrapper">
                    <Fingerprint className="verification-spinner-inner" size={32} style={{ color: 'var(--color-accent-danger, #ef4444)' }} />
                </div>
                <p className="verification-text">Service Unreachable. Please check your connection.</p>
                <button
                    className="wizard-btn-secondary"
                    onClick={() => window.location.reload()}
                    style={{ marginTop: '1rem', padding: '0.6rem 1.2rem', borderRadius: '8px' }}
                >
                    Retry Connection
                </button>
            </div>
        );
    }

    // 3) Initial role load only (userRole was never set yet) → show spinner
    //    If userRole is already populated, DON'T unmount children during a background
    //    re-verification (e.g. Supabase token refresh on tab-focus). This keeps the
    //    WizardManager mounted and preserves all in-progress form data.
    if (roleLoading && !userRole) {
        return (
            <div className="verification-container">
                <div className="verification-spinner-wrapper">
                    <div className="verification-spinner-circle" />
                    <Fingerprint className="verification-spinner-inner" size={32} />
                </div>
                <p className="verification-text">Verifying access...</p>
            </div>
        );
    }

    // 4) Role loaded but not a student → redirect
    if (userRole && userRole.is_student !== true) {
        if (userRole.is_staff || userRole.is_superuser) {
            return <Navigate to="/admin" replace />;
        }
        return <Navigate to="/signin?error=unauthorized" replace />;
    }

    return children;
};

export default ProtectedRoute;

