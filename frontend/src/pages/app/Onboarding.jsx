import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
    Sparkles, BookOpen, Target, ArrowRight,
    GraduationCap, Brain, Star
} from 'lucide-react';
import './Onboarding.css';


const steps = [
    {
        icon: <GraduationCap size={32} />,
        title: 'Enter Your KCSE Results',
        desc: 'Tell us your subjects and grades so our AI can calculate your cluster points and eligibility.',
        color: 'cyan',
    },
    {
        icon: <Brain size={32} />,
        title: 'Share Your Interests & Goals',
        desc: 'What careers excite you? What are your priorities — salary, passion, location, budget?',
        color: 'violet',
    },
    {
        icon: <Star size={32} />,
        title: 'Get AI-Powered Recommendations',
        desc: 'Our engine matches your profile to real KUCCPS programmes at institutions you can actually get into.',
        color: 'amber',
    },
];

const Onboarding = () => {
    const { user } = useAuth();
    const navigate = useNavigate();

    const displayName = user?.user_metadata?.full_name
        || user?.user_metadata?.name
        || 'Scholar';

    return (
        <div className="onboarding-page">
            <div className="onboarding-bg-blur onboarding-blur-1" />
            <div className="onboarding-bg-blur onboarding-blur-2" />

            <div className="onboarding-content">
                {/* Header */}
                <div className="onboarding-header">
                    <span className="onboarding-badge">
                        <Sparkles size={14} />
                        Welcome to KeDira | PROACTEDAI
                    </span>
                    <h1 className="onboarding-title">
                        Hey {displayName.split(' ')[0]}, let's map your future 🎓
                    </h1>
                    <p className="onboarding-subtitle">
                        You're just a few steps away from your personalised academic roadmap.
                        Here's what happens next:
                    </p>
                </div>

                {/* Steps */}
                <div className="onboarding-steps">
                    {steps.map((step, i) => (
                        <div className={`onboarding-step-card color-${step.color}`} key={i}>
                            <div className={`step-icon-box ${step.color}`}>
                                {step.icon}
                            </div>
                            <div className="step-number">Step {i + 1}</div>
                            <h3 className="step-title">{step.title}</h3>
                            <p className="step-desc">{step.desc}</p>
                        </div>
                    ))}
                </div>

                {/* CTA */}
                <div className="onboarding-cta-area">
                    <button
                        className="onboarding-cta-btn"
                        onClick={() => navigate('/app/new')}
                        id="onboarding-start-btn"
                    >
                        <BookOpen size={20} />
                        Start My Assessment
                        <ArrowRight size={20} />
                    </button>
                    <p className="onboarding-cta-note">
                        <Target size={14} />
                        Takes about 5–10 minutes. Your data is saved automatically.
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Onboarding;
