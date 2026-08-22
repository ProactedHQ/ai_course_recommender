import { ShieldCheck, CheckCircle2, Brain, Calculator, Save, History, Sparkles, Zap } from 'lucide-react';
import Navbar from '../Navbar';
import Footer from '../Footer';
import './AuthLayout.css';

const AuthLayout = ({ children, title, subtitle, badge, benefitsTitle, benefits }) => {

    const getBenefitIcon = (text) => {
        const t = text.toLowerCase();
        if (t.includes("recommendations")) return <Brain size={20} className="benefit-icon-premium" />;
        if (t.includes("cluster points") || t.includes("calculation")) return <Calculator size={20} className="benefit-icon-premium" />;
        if (t.includes("kuccps") || t.includes("eligibility") || t.includes("matching")) return <ShieldCheck size={20} className="benefit-icon-premium" />;
        if (t.includes("save")) return <Save size={20} className="benefit-icon-premium" />;
        if (t.includes("revisit")) return <History size={20} className="benefit-icon-premium" />;
        return <CheckCircle2 size={20} className="benefit-icon-premium" />;
    };

    return (
        <div className="auth-page-wrapper">
            <Navbar />

            <main className="auth-main-content">
                <div className="auth-container-frame">
                    <div className="auth-grid">
                        {/* Left Column: Form */}
                        <div className="auth-form-column">
                            <div className="auth-header-area">
                                <div className="auth-title-row">
                                    <h1 className="auth-primary-title">{title}</h1>
                                    {badge && <span className="auth-plan-badge">{badge}</span>}
                                </div>
                                {subtitle && <p className="auth-secondary-subtitle">{subtitle}</p>}
                            </div>

                            <div className="auth-form-body">
                                {children}
                            </div>
                        </div>

                        {/* Right Column: Value Panel */}
                        <div className="auth-value-column">
                            {/* CSS-based Hero Visual */}
                            <div className="auth-hero-visual">
                                <div className="hero-glow-orb orb-1"></div>
                                <div className="hero-glow-orb orb-2"></div>
                                <div className="hero-icon-container">
                                    <Sparkles size={48} className="hero-main-icon" strokeWidth={1.5} />
                                    <div className="hero-floating-icon float-1"><Brain size={20} /></div>
                                    <div className="hero-floating-icon float-2"><QuoteIcon size={16} /></div>
                                </div>
                            </div>

                            <div className="value-panel-content">
                                <h2 className="value-panel-title">{benefitsTitle}</h2>
                                <ul className="value-benefits-list">
                                    {benefits.map((benefit, index) => (
                                        <li key={index} className="value-benefit-item">
                                            <div className="benefit-icon-wrapper">
                                                {getBenefitIcon(benefit)}
                                            </div>
                                            <span className="benefit-text">{benefit}</span>
                                        </li>
                                    ))}
                                </ul>

                                <div className="value-security-note">
                                    <ShieldCheck className="security-icon-premium" size={20} />
                                    <p>Your data is private and securely stored.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>

            <Footer />
        </div>
    );
};

const QuoteIcon = ({ size }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V20c0 1 0 1 1 1z" />
        <path d="M15 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2h-4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V20c0 1 0 1 1 1z" />
    </svg>
);

export default AuthLayout;
