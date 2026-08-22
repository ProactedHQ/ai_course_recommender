import { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { Stars, Gift, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import AuthLayout from '../../components/layout/AuthLayout';
import './Auth.css';

const SignUp = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { signup, loginWithGoogle, selectPlan } = useAuth();

  const plan = searchParams.get('plan') || 'free';
  const rawReturnTo = searchParams.get('returnTo') || '/app';
  // Sanitize returnTo: must start with / and not be a full URL
  const returnTo = rawReturnTo.startsWith('/') && !rawReturnTo.includes('://') ? rawReturnTo : '/app';

  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    agreeToTerms: false
  });

  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    if (plan) selectPlan(plan);
  }, [plan, selectPlan]);


  const handleGoogleLogin = async () => {
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
    "Personalized course recommendations",
    "Cluster points calculation",
    "KUCCPS-aligned eligibility checks",
    "Save and revisit results"
  ];

  const planBadge = (() => {
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

    // ... (rest of validation) ...
    if (!formData.fullName.trim()) {
      setError('Full Name is required');
      return;
    }

    if (!formData.email.trim()) {
      setError('Email address is required');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError('Please enter a valid email address');
      return;
    }

    if (!formData.password) {
      setError('Password is required');
      return;
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    if (!formData.confirmPassword) {
      setError('Please confirm your password');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (!formData.agreeToTerms) {
      setError('You must agree to the Terms and Privacy Policy');
      return;
    }

    setIsLoading(true);

    try {
      const data = await signup(formData.email, formData.password);

      if (data?.user && !data?.session) {
        setSuccessMessage(`A confirmation link has been sent to ${formData.email}. Please check your inbox and click the link to confirm your account.`);
        return;
      }

      // If paid plan, go to subscription for payment, otherwise go to onboarding/returnTo
      const destination = (plan === 'standard' || plan === 'premium')
        ? '/app/subscription?auto=1'
        : returnTo;

      navigate(destination);
    } catch (err) {
      // ... (error handling) ...
      console.error('[SignUp] Error:', err);
      let userMessage = 'Something went wrong during sign-up';

      if (err.message?.includes('User already registered')) {
        userMessage = 'An account with this email already exists.';
      } else if (err.message?.includes('rate limit')) {
        userMessage = 'Too many sign-up attempts. Please try again later.';
      } else if (err.message) {
        userMessage = err.message;
      }

      setError(userMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout
      title={successMessage ? "Check your email" : "Create your account"}
      subtitle={successMessage ? "We've sent you a confirmation link." : (plan !== 'free' ? "Experience the full power of KeDira." : "Join thousands of students finding their perfect course match.")}
      badge={planBadge}
      benefitsTitle="Why join us?"
      benefits={benefits}
    >
      {successMessage ? (
        <div className="form-success-text feedback-box success" style={{ padding: '2rem', textAlign: 'center', marginTop: '1rem' }}>
          <h4>Registration Successful!</h4>
          <p style={{ marginTop: '0.5rem', marginBottom: '1.5rem', lineHeight: '1.5' }}>{successMessage}</p>
          <Link to="/signin" className="btn-auth-primary" style={{ display: 'inline-block', textDecoration: 'none' }}>
            Go to Sign In
          </Link>
        </div>
      ) : (
      <form onSubmit={handleSubmit} noValidate>
        {error && (
          <div className="form-error-text feedback-box error">
            {error}
          </div>
        )}

        <div className="form-group">
          <label className="form-label" htmlFor="fullName">Full Name</label>
          <input
            id="fullName"
            type="text"
            className="form-input"
            required
            autoComplete="name"
            value={formData.fullName}
            onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
            placeholder="Mkenya Halisi"
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="email">Email Address</label>
          <input
            id="email"
            type="email"
            className="form-input"
            required
            autoComplete="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            placeholder="mkenya@gmail.com"
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="password">Password</label>
          <div className="form-input-wrapper">
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              className="form-input"
              required
              autoComplete="new-password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              placeholder="At least 8 characters"
            />
            <button
              type="button"
              className="password-toggle-btn"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
          <p className="form-helper-text">At least 8 characters</p>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="confirmPassword">Confirm Password</label>
          <div className="form-input-wrapper">
            <input
              id="confirmPassword"
              type={showPassword ? "text" : "password"}
              className="form-input"
              required
              autoComplete="new-password"
              value={formData.confirmPassword}
              onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
              placeholder="Re-enter your password"
            />
          </div>
        </div>

        <div className="form-group terms-checkbox-row">
          <input
            id="terms"
            type="checkbox"
            checked={formData.agreeToTerms}
            onChange={(e) => setFormData({ ...formData, agreeToTerms: e.target.checked })}
          />

          <label htmlFor="terms" className="terms-text">
            I agree to <Link to="/terms-of-service" target="_blank">Terms of Service</Link> & <Link to="/privacy-policy" target="_blank">Privacy Policy</Link>
          </label>
        </div>

        <button
          type="submit"
          className="btn-auth-primary"
          disabled={isLoading}
        >
          {isLoading ? "Creating account..." : "Create account"}
        </button>

        <div className="auth-form-divider">OR</div>

        <button
          type="button"
          className="btn-auth-social"
          disabled={isLoading}
          onClick={handleGoogleLogin}
        >
          <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google" className="social-icon" />
          Sign up with Google
        </button>

        <div className="auth-footer-link">
          Already have an account? <Link to="/signin">Sign in</Link>
        </div>
      </form>
      )}

      <div className="plan-info-box">
        <p className="plan-info-text">
          {plan === 'premium' ? (
            <>
              <Stars size={16} className="plan-info-icon" />
              <span>Premium includes unlimited prompts + detailed analysis</span>
            </>
          ) : (
            <>
              <Gift size={16} className="plan-info-icon" />
              <span>Free plan includes 1 prompt</span>
            </>
          )}
        </p>
      </div>
    </AuthLayout>
  );
};

export default SignUp;
