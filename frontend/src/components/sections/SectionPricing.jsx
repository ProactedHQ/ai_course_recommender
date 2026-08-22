import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { Check, Sparkles, Zap, Crown, ArrowRight } from "lucide-react";
import "./SectionPricing.css";

const SectionPricing = () => {
    const { user, selectPlan } = useAuth();
    const navigate = useNavigate();

    const handleSelectPlan = (plan) => {
        selectPlan(plan);
        if (!user) {
            navigate(`/signup?plan=${plan}`);
        } else {
            navigate("/app/subscription");
        }
    };

    const handleStartFree = () => {
        selectPlan("free");
        navigate("/signup");
    };

    return (
        <section className="section-outer pricing-section" id="pricing">
            <div className="section-inner">
                <header className="pricing-header">
                    <h2 className="section-title">Investment in Your Future</h2>
                    <p className="section-subtitle">Choose the perfect plan to navigate your academic and career journey.</p>
                </header>

                <div className="pricing-grid">
                    {/* Explorer Tier */}
                    <div className="pricing-card tier-free">
                        <div className="tier-badge">100% FREE</div>
                        <div className="card-top-inner">
                            <div className="tier-icon"><Zap size={24} /></div>
                            <h3 className="plan-name">Explorer</h3>
                            <p className="plan-desc">Essential matching for every student.</p>
                            <div className="price-stack">
                                <span className="old-price">KES 399</span>
                                <div className="plan-price">
                                    <span className="p-curr">KES</span>
                                    <span className="p-amt">0</span>
                                    <span className="p-per">/year</span>
                                </div>
                            </div>
                        </div>
                        <ul className="plan-features">
                            <li><Check size={18} /> 1 AI-Powered Prompt per month</li>
                            <li><Check size={18} /> Basic course matching based on grades & interests</li>
                            <li><Check size={18} /> Official KUCCPS program codes after recommendation</li>
                            <li><Check size={18} /> Core institution discovery (public & private)</li>
                            <li><Check size={18} /> Standard email support (48-hour response)</li>
                        </ul>
                        <button className="path-btn secondary" onClick={handleStartFree}>
                            Start Journey <ArrowRight size={18} className="btn-icon-right" />
                        </button>
                    </div>

                    {/* Mentor Elite Tier */}
                    <div className="pricing-card tier-standard highlighted">
                        <div className="tier-badge">80% OFF</div>
                        <div className="card-top-inner">
                            <div className="tier-icon primary"><Sparkles size={24} className="animate-pulse" /></div>
                            <h3 className="plan-name">Mentor Elite</h3>
                            <p className="plan-desc">Elite performance for serious scholars.</p>
                            <div className="price-stack">
                                <span className="old-price">KES 999</span>
                                <div className="plan-price">
                                    <span className="p-curr">KES</span>
                                    <span className="p-amt">199</span>
                                    <span className="p-per">/year</span>
                                </div>
                            </div>
                        </div>
                        <ul className="plan-features">
                            <li><Check size={18} /> 5 AI-Powered Prompts per month</li>
                            <li><Check size={18} /> Official KUCCPS program codes</li>
                            <li><Check size={18} /> Detailed course discovery with trade-off analysis</li>
                            <li><Check size={18} /> Career path preview (salary, stability, growth)</li>
                            <li><Check size={18} /> Personalized compatibility score</li>
                            <li><Check size={18} /> Priority email support (12-hour response)</li>
                        </ul>
                        <button className="path-btn primary" onClick={() => handleSelectPlan("standard")}>
                            Elevate Now <Sparkles size={18} className="btn-icon-right" />
                        </button>
                    </div>

                    {/* Scholar VVIP Tier */}
                    <div className="pricing-card tier-premium dominant">
                        <div className="tier-badge premium">79% OFF</div>
                        <div className="card-top-inner">
                            <div className="tier-icon superior"><Crown size={28} /></div>
                            <h3 className="plan-name">Scholar VVIP</h3>
                            <p className="plan-desc">Ultimate intelligence for career success.</p>
                            <div className="price-stack">
                                <span className="old-price">KES 2,499</span>
                                <div className="plan-price">
                                    <span className="p-curr">KES</span>
                                    <span className="p-amt">499</span>
                                    <span className="p-per">/year</span>
                                </div>
                            </div>
                        </div>
                        <ul className="plan-features">
                            <li><Check size={18} /> Unlimited AI-Powered Prompts</li>
                            <li><Check size={18} /> Advanced AI compatibility matching</li>
                            <li><Check size={18} /> Official KUCCPS codes + real-time cluster mapping</li>
                            <li><Check size={18} /> Full institution comparison dashboard</li>
                            <li><Check size={18} /> Detailed career roadmap (5-10 year projections)</li>
                            <li><Check size={18} /> Official KUCCPS portal application support (We apply for you)</li>
                            <li><Check size={18} /> 24/7 priority VIP support (Exclusive VVIP WhatsApp)</li>
                            <li><Check size={18} /> Early access to new features</li>
                        </ul>
                        <button className="path-btn premium" onClick={() => handleSelectPlan("premium")}>
                            Go VVIP <Crown size={18} className="btn-icon-right" />
                        </button>
                    </div>
                </div>

                <div className="pricing-sales-contact">
                    <p>Want to talk to sales? <a href="tel:+254743720033">+254 743 720 033</a></p>
                </div>
            </div>
        </section>
    );
};

export default SectionPricing;
