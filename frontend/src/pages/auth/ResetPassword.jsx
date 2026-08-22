import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import AuthLayout from '../../components/layout/AuthLayout';
import './Auth.css';

const ResetPassword = () => {
    const navigate = useNavigate();
    const { updatePassword } = useAuth();
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (password.length < 8) {
            setError('Password must be at least 8 characters long');
            return;
        }

        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        setIsLoading(true);
        try {
            await updatePassword(password);
            setSuccess(true);
            setTimeout(() => navigate('/signin'), 3000);
        } catch (err) {
            setError(err.message || 'Failed to update password');
        } finally {
            setIsLoading(false);
        }
    };

    const benefits = [
        "Secure your account with a new password",
        "Keep your profile and history safe",
        "Restore access to your course matches"
    ];

    if (success) {
        return (
            <AuthLayout
                title="Password Updated"
                subtitle="Your password has been reset successfully. Redirecting you to sign in..."
                benefits={benefits}
            >
                <div className="flex justify-center p-8">
                    <div className="text-teal-600 font-bold">✓ Success</div>
                </div>
            </AuthLayout>
        );
    }

    return (
        <AuthLayout
            title="Set New Password"
            subtitle="Please enter your new password below."
            benefits={benefits}
        >
            <form onSubmit={handleSubmit} noValidate>
                {error && (
                    <div className="form-error-text" style={{ padding: '12px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '8px', marginBottom: '16px' }}>
                        {error}
                    </div>
                )}

                <div className="form-group">
                    <label className="form-label" htmlFor="password">New Password</label>
                    <input
                        id="password"
                        type="password"
                        className="form-input"
                        required
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="At least 8 characters"
                    />
                </div>

                <div className="form-group">
                    <label className="form-label" htmlFor="confirmPassword">Confirm New Password</label>
                    <input
                        id="confirmPassword"
                        type="password"
                        className="form-input"
                        required
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        placeholder="Re-enter password"
                    />
                </div>

                <button
                    type="submit"
                    className="btn-auth-primary"
                    disabled={isLoading}
                >
                    {isLoading ? "Updating..." : "Update Password"}
                </button>
            </form>
        </AuthLayout>
    );
};

export default ResetPassword;
