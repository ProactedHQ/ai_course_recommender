import { useNavigate } from 'react-router-dom';
import { X, ShieldAlert } from 'lucide-react';
import '../../styles/AdminTheme.css';

const ImpersonationBanner = () => {
    const navigate = useNavigate();
    const isImpersonating = localStorage.getItem('admin_impersonation_active') === 'true';
    const impersonatedEmail = localStorage.getItem('impersonated_user_email');

    const handleExitImpersonation = () => {
        // Clear impersonation flags
        localStorage.removeItem('admin_impersonation_active');
        localStorage.removeItem('admin_return_token');
        localStorage.removeItem('impersonated_user_email');

        // Return to admin panel
        navigate('/admin/users');
        window.location.reload();
    };

    if (!isImpersonating) return null;

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            zIndex: 9999,
            background: 'linear-gradient(135deg, var(--admin-accent-danger), var(--admin-accent-warning))',
            color: 'white',
            padding: '1rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '1rem',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
        }}>
            <ShieldAlert size={20} />
            <div style={{ flex: 1, textAlign: 'center', fontWeight: 600 }}>
                You are currently impersonating: <strong>{impersonatedEmail}</strong>
            </div>
            <button
                onClick={handleExitImpersonation}
                style={{
                    background: 'white',
                    color: 'var(--admin-accent-danger)',
                    border: 'none',
                    padding: '0.5rem 1rem',
                    borderRadius: '6px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem'
                }}
            >
                <X size={16} />
                Exit Impersonation
            </button>
        </div>
    );
};

export default ImpersonationBanner;
