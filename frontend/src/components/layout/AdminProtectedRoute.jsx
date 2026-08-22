import { Navigate, useLocation } from 'react-router-dom';
import { ShieldCheck } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const AdminProtectedRoute = ({ children }) => {
    const { user, userRole, roleLoading, networkError } = useAuth();
    const location = useLocation();

    // 1) Not authenticated at all → sign in
    if (!user) {
        return <Navigate to={`/signin?returnTo=${location.pathname}`} replace />;
    }

    // 2) Still fetching role or Network Error → show verification or error UI
    if (roleLoading || networkError || !userRole) {
        return (
            <div className="verification-container">
                <div className="verification-spinner-wrapper">
                    {networkError ? (
                        <ShieldCheck className="verification-spinner-inner" size={32} style={{ color: 'var(--admin-accent-danger)' }} />
                    ) : (
                        <>
                            <div className="verification-spinner-circle" />
                            <ShieldCheck className="verification-spinner-inner" size={32} />
                        </>
                    )}
                </div>
                <p className="verification-text">
                    {networkError ? 'Service Unreachable. Please check your connection.' : 'Verifying admin access...'}
                </p>
                {networkError && (
                    <button
                        className="admin-btn admin-btn-secondary"
                        onClick={() => window.location.reload()}
                        style={{ marginTop: '1rem' }}
                    >
                        Retry Connection
                    </button>
                )}
            </div>
        );
    }

    // 3) Backend-verified check: must be staff AND not a student
    const isAdmin = userRole.is_staff === true && userRole.is_student === false;

    if (!isAdmin) {
        // Students and non-staff users → redirect to app
        return <Navigate to="/app?error=unauthorized" replace />;
    }

    return children;
};

export default AdminProtectedRoute;
