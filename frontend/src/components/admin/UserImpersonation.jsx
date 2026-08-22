import { useState } from 'react';
import { UserCog, AlertTriangle, LogIn } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import adminApi from '../../api/adminApi';
import '../../styles/AdminTheme.css';

const UserImpersonation = ({ userId, userEmail, onClose }) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    const handleImpersonate = async () => {
        const confirmed = window.confirm(
            `Are you sure you want to impersonate ${userEmail}?\n\n` +
            `This will log you in as this user. Your admin session will be stored and you can return to admin mode later.`
        );

        if (!confirmed) return;

        try {
            setLoading(true);
            const result = await adminApi.impersonateUser(userId);

            // Store admin session for later restoration
            localStorage.setItem('admin_impersonation_active', 'true');
            localStorage.setItem('admin_return_token', result.adminToken);
            localStorage.setItem('impersonated_user_email', userEmail);

            // Navigate to user's app view
            navigate('/app');
            window.location.reload(); // Reload to apply impersonation

        } catch (err) {
            console.error('Impersonation failed:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="admin-card" style={{ marginTop: '1.5rem' }}>
            <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
                marginBottom: '1rem'
            }}>
                <div className="admin-stat-icon warning">
                    <UserCog size={20} />
                </div>
                <div>
                    <h3 style={{ margin: 0, color: 'var(--admin-text-primary)' }}>
                        User Impersonation
                    </h3>
                    <p style={{
                        margin: 0,
                        marginTop: '0.25rem',
                        fontSize: '0.875rem',
                        color: 'var(--admin-text-muted)'
                    }}>
                        View the application as this user for debugging
                    </p>
                </div>
            </div>

            {error && (
                <div style={{
                    padding: '1rem',
                    background: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid var(--admin-accent-danger)',
                    borderRadius: '8px',
                    marginBottom: '1rem',
                    display: 'flex',
                    gap: '0.75rem',
                    alignItems: 'start'
                }}>
                    <AlertTriangle size={18} color="var(--admin-accent-danger)" />
                    <div>
                        <div style={{ fontWeight: 600, color: 'var(--admin-accent-danger)' }}>
                            Impersonation Failed
                        </div>
                        <div style={{ fontSize: '0.875rem', color: 'var(--admin-text-muted)', marginTop: '0.25rem' }}>
                            {error}
                        </div>
                    </div>
                </div>
            )}

            <div style={{
                padding: '1rem',
                background: 'rgba(245, 158, 11, 0.1)',
                border: '1px solid var(--admin-accent-warning)',
                borderRadius: '8px',
                marginBottom: '1rem'
            }}>
                <div style={{
                    display: 'flex',
                    gap: '0.75rem',
                    alignItems: 'start'
                }}>
                    <AlertTriangle size={18} color="var(--admin-accent-warning)" />
                    <div style={{ fontSize: '0.875rem', color: 'var(--admin-text-secondary)' }}>
                        <strong>Warning:</strong> Impersonating a user will log you in as them.
                        All actions will be logged for audit purposes. You can return to admin
                        mode by clicking the "Exit Impersonation" banner that will appear.
                    </div>
                </div>
            </div>

            <button
                className="admin-btn admin-btn-primary"
                onClick={handleImpersonate}
                disabled={loading}
            >
                <LogIn size={18} />
                {loading ? 'Starting Impersonation...' : `Impersonate ${userEmail}`}
            </button>
        </div>
    );
};

export default UserImpersonation;
