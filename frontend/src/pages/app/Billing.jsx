import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { CreditCard } from 'lucide-react';

/**
 * Billing page — immediately redirects to /app/subscription
 * where plan management and payments (via KeDira's backend) live.
 */
const Billing = () => {
    const navigate = useNavigate();

    useEffect(() => {
        navigate('/app/subscription', { replace: true });
    }, [navigate]);

    // Minimal fallback shown for a split-second before redirect
    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '60vh',
            gap: '1rem',
            color: 'var(--text-secondary, #aaa)'
        }}>
            <CreditCard size={40} />
            <p>Redirecting to billing…</p>
        </div>
    );
};

export default Billing;
