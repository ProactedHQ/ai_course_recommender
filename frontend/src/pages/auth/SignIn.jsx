import { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { apiFetch } from '../../lib/apiClient';
import AuthLayout from '../../components/layout/AuthLayout';
import './Auth.css';

const SignIn = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login, loginWithGoogle, resetPassword } = useAuth();

  const rawReturnTo = searchParams.get('returnTo') || '/app';
  // Sanitize returnTo: must start with / and not be a full URL
  const returnTo = rawReturnTo.startsWith('/') && !rawReturnTo.includes('://') ? rawReturnTo : '/app';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false); // Default to false
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // ── Init: Load saved email if previously remembered ──
  useEffect(() => {
    const savedEmail = localStorage.getItem('supabase.saved_email');
    if (savedEmail) {
      setEmail(savedEmail);
    }
    // Note: We explicitly do NOT set rememberMe to true here.
    // The user must manually check it every time they want to be remembered.
  }, []);


  const plan = searchParams.get('plan');

  const planBadge = (() => {
    if (!plan) return null;
    switch (plan) {
      case 'standard':
        return <span className="auth-plan-badge premium">Mentor Elite • KES 199/month</span>;
      case 'premium':
        return <span className="auth-plan-badge premium">Scholar VVIP • KES 499/month</span>;
      default:
        return <span className="auth-plan-badge">Explorer • Free</span>;
    }
  })();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    // ... (rest of validation) ...
    if (!email.trim()) {
      setError('Email address is required');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError('Please enter a valid email address');
      return;
    }

    if (!password) {
      setError('Password is required');
      return;
    }

    setIsLoading(true);

    try {
      // ── Handle Remember Me Persistence ──
      if (rememberMe) {
        localStorage.setItem('supabase.saved_email', email);
      } else {
        localStorage.removeItem('supabase.saved_email');
      }

      await login(email, password);

      // Fetch backend-verified role (source of truth)
      const roleData = await apiFetch('/api/auth/me/');

      const isStaff = roleData.is_staff === true && roleData.is_student === false;

      if (isStaff) {
        navigate('/admin/dashboard');
        return;
      }

      // If paid plan, go to subscription for payment
      if (plan === 'standard' || plan === 'premium') {
        navigate('/app/subscription?auto=1');
        return;
      }

      // Student: block returnTo=/admin/* paths
      const safeReturnTo = returnTo.startsWith('/admin') ? '/app' : returnTo;
      navigate(safeReturnTo);
    } catch (err) {
      // ... (error handling) ...
      console.error('[SignIn] Error:', err);
      // Map specific Supabase/Backend errors to user-friendly messages
      let userMessage = 'Invalid email or password';

      if (err.message?.includes('Invalid login credentials')) {
        userMessage = 'Incorrect email or password. Please try again.';
      } else if (err.message?.includes('Email not confirmed')) {
        userMessage = 'Please confirm your email address before signing in.';
      } else if (err.status === 403) {
        userMessage = 'Your account does not have permission to access this area.';
      } else if (err.message?.includes('rate limit')) {
        userMessage = 'Too many sign-in attempts. Please try again later.';
      }

      setError(userMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleForgotPassword = async (e) => {
    // ...
    e.preventDefault();
    if (!email) {
      setError('Please enter your email address first.');
      return;
    }
    setError('');
    setSuccess('');
    setIsLoading(true);
    try {
      await resetPassword(email);
      setSuccess(`If an account exists for ${email}, a password reset link has been sent. Check your inbox (and spam folder). The link expires shortly`);
    } catch (err) {
      setError(err.message || 'Failed to send reset link.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    // ...
    try {
      setError('');
      setIsLoading(true);
      await loginWithGoogle();
    } catch (err) {
      setError(err.message || 'Google sign-in failed');
      setIsLoading(false);
    }
  };

  const benefits = [
    "Save your KCSE results and preferences",
    "Get KUCCPS-aligned matching",
    "Revisit recommendations anytime"
  ];

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Sign in to continue your course matching journey."
      badge={planBadge}
      benefitsTitle="Why sign in?"
      benefits={benefits}
    >
      <form onSubmit={handleSubmit} noValidate>
        {success && (
          <div className="form-success-text feedback-box success">
            {success}
          </div>
        )}

        {error && (
          <div className="form-error-text feedback-box error">
            {error}
          </div>
        )}

        <div className="form-group">
          <label className="form-label" htmlFor="email">Email Address</label>
          <input
            id="email"
            type="email"
            className={`form-input ${error ? 'error' : ''}`}
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="mkenya@gmail.com"
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="password">Password</label>
          <div className="form-input-wrapper">
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              className={`form-input ${error ? 'error' : ''}`}
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
            />
            <button
              type="button"
              className="password-toggle-btn"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </div>

        <div className="auth-utility-row">
          <label className="remember-me-label">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
            />
            <span>Remember me</span>
          </label>
          <button
            type="button"
            className="forgot-password-link-btn"
            onClick={handleForgotPassword}
          >
            Forgot password?
          </button>
        </div>

        <button
          type="submit"
          className="btn-auth-primary"
          disabled={isLoading}
        >
          {isLoading ? "Signing in..." : "Sign in"}
        </button>

        <div className="auth-form-divider">OR</div>

        <button
          type="button"
          className="btn-auth-social"
          disabled={isLoading}
          onClick={handleGoogleLogin}
        >
          <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google" className="social-icon" />
          Continue with Google
        </button>

        <div className="auth-footer-link">
          Don't have an account? <Link to="/signup">Create an account</Link>
        </div>
      </form>
    </AuthLayout>
  );
};

export default SignIn;
