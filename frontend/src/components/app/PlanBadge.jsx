import React from 'react';
import { useNavigate } from 'react-router-dom';
import './PlanBadge.css';

const PlanBadge = ({ plan = 'free' }) => {
    const navigate = useNavigate();

    const getPlanStyles = () => {
        switch (plan?.toLowerCase()) {
            case 'scholar_vvip':
            case 'premium':
                return { label: 'Scholar VVIP', className: 'badge-gold' };
            case 'mentor_elite':
            case 'standard':
                return { label: 'Mentor Elite', className: 'badge-premium' };
            case 'explorer':
            case 'free':
            default:
                return { label: 'Explorer', className: 'badge-free' };
        }
    };

    const { label, className } = getPlanStyles();

    return (
        <div className={`plan-badge-container ${className}`}>
            <span className="badge-text">{label}</span>
            {plan === 'free' && (
                <button
                    className="upgrade-btn"
                    onClick={() => navigate('/app/subscription')}
                >
                    Upgrade
                </button>
            )}
        </div>
    );
};

export default PlanBadge;
