import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { apiFetch } from '../../lib/apiClient';
import {
    Check, Zap, Crown, Sparkles,
    ArrowRight, ShieldCheck, Heart, Users,
    CreditCard, X, Phone, Copy, CheckCircle2, Ticket
} from 'lucide-react';
import './Subscription.css';

const MPesaIcon = () => (
    <div className="mpesa-logo-ultra">
        <svg viewBox="0 0 180 40" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M5 35V5H14L19 18L24 5H33V35H27V15L19 35H18L10 15V35H5Z" fill="#4fb347" />
            <circle cx="43" cy="20" r="5" fill="#ee1c25" />
            <path d="M55 35V5H72C80 5 83 10 83 15C83 20 80 25 72 25H62V35H55ZM62 19H72C76 19 76 11 72 11H62V19Z" fill="#4fb347" />
            <path d="M90 35V5H110V11H97V17H108V23H97V29H110V35H90Z" fill="#4fb347" />
            <path d="M128 30C123 30 120 28 118 25L123 21C124 23 126 24 128 24C131 24 132 23 132 21C132 19 131 18 126 17C120 15 116 13 116 8C116 3 121 0 128 0C134 0 138 2 141 6L136 10C135 8 132 6 128 6C125 6 123 7 123 9C123 11 125 12 130 13C136 15 140 17 140 22C140 27 136 30 128 30Z" transform="translate(0, 5)" fill="#4fb347" />
            <path d="M148 35L160 5H168L180 35H173L170 27H158L155 35H148ZM160 21H168L164 11L160 21Z" fill="#4fb347" />
        </svg>
    </div>
);

// How long to wait for PayHero's callback before giving up on a payment.
const POLL_TIMEOUT_MS = 2 * 60 * 1000;

const Subscription = () => {
    const { subscription, refreshAuth, loading: authLoading } = useAuth();
    const [upgrading, setUpgrading] = useState(null);
    const [showMpesaModal, setShowMpesaModal] = useState(false);
    const [selectedPlanForUpgrade, setSelectedPlanForUpgrade] = useState(null);
    const [phoneNumber, setPhoneNumber] = useState('');
    const [couponInput, setCouponInput] = useState('');
    const [pollingTxn, setPollingTxn] = useState(null);
    const [error, setError] = useState(null);
    const [couponCode, setCouponCode] = useState(null);
    const [generatingCoupon, setGeneratingCoupon] = useState(false);
    const [copied, setCopied] = useState(false);
    const [showVvipModal, setShowVvipModal] = useState(false);
    const [vvipStatus, setVvipStatus] = useState('pending'); // 'pending', 'consented'

    const currentTier = subscription.tier;

    // Mapping for UI vs Backend
    const PLAN_MAP = {
        'explorer': 'free',
        'mentor_elite': 'standard',
        'scholar_vvip': 'premium'
    };

    const REVERSE_MAP = {
        'free': 'explorer',
        'standard': 'mentor_elite',
        'premium': 'scholar_vvip'
    };

    const initiateSTKPush = async () => {
        if (!phoneNumber || !selectedPlanForUpgrade) return;

        console.log(`[Subscription] Initiating STK push: phone=${phoneNumber}, plan=${selectedPlanForUpgrade}`);
        setError(null);
        setUpgrading(selectedPlanForUpgrade);
        setShowMpesaModal(false);

        try {
            const targetTier = REVERSE_MAP[selectedPlanForUpgrade];
            // 1. Initiate Upgrade
            const response = await apiFetch('/api/subscriptions/initiate/', {
                method: 'POST',
                body: {
                    target_tier: targetTier,
                    phone_number: phoneNumber,
                    coupon: couponInput // Optional coupon
                }
            });

            console.log('[Subscription] Initiate response received:', response);
            const txn = response.external_reference; // Match the new backend response field or use reference
            console.log(`[Subscription] External Reference: ${txn}`);
            setPollingTxn(response); // Store the whole response to have access to whatever field we need

        } catch (err) {
            console.error('[Subscription] Upgrade failed:', err);
            setError(err.message || 'Upgrade failed. Please try again.');
            setUpgrading(null);
        }
    };

    // Polling effect: after initiate/, ask the backend every 3s whether PayHero's
    // callback has arrived (GET /api/subscriptions/status/). Gives up after
    // POLL_TIMEOUT_MS so an unanswered STK push doesn't poll forever.
    useEffect(() => {
        let interval;
        if (pollingTxn) {
            console.log("[Subscription] Polling started for transaction status...");
            const startedAt = Date.now();
            interval = setInterval(async () => {
                if (Date.now() - startedAt > POLL_TIMEOUT_MS) {
                    clearInterval(interval);
                    setPollingTxn(null);
                    setUpgrading(null);
                    setError('We did not receive a payment confirmation. If you completed the M-Pesa prompt, refresh this page in a minute to see your plan.');
                    return;
                }
                try {
                    // Changed to GET as per the refactored backend view
                    const statusRes = await apiFetch('/api/subscriptions/status/', {
                        method: 'GET'
                    });

                    console.log(`[Subscription] Polled status: ${statusRes.status}`, statusRes);

                    if (statusRes.status === 'completed') {
                        console.log('[Subscription] Payment successful! Stopping polling.');
                        clearInterval(interval);
                        setPollingTxn(null);
                        setUpgrading(null);
                        await refreshAuth();
                        if (selectedPlanForUpgrade === 'premium') {
                            setShowVvipModal(true);
                        } else {
                            alert('Upgrade successful! Your account has been updated.');
                        }
                    } else if (statusRes.status === 'failed') {
                        console.log('[Subscription] Payment failed. Stopping polling.');
                        clearInterval(interval);
                        setPollingTxn(null);
                        setUpgrading(null);
                        setError(statusRes.message || 'Payment failed. Please try again.');
                    } else {
                        console.log('[Subscription] Payment still pending...');
                    }
                } catch (err) {
                    console.error('[Subscription] Polling error:', err);
                }
            }, 3000); // Check every 3s
        }
        return () => {
            if (interval) {
                console.log("[Subscription] Cleaning up polling interval.");
                clearInterval(interval);
            }
        };
    }, [pollingTxn, refreshAuth]);

    // Error auto-dismiss
    useEffect(() => {
        if (error) {
            const timer = setTimeout(() => {
                setError(null);
            }, 6000);
            return () => clearTimeout(timer);
        }
    }, [error]);

    const handleUpgradeClick = (plan) => {
        setSelectedPlanForUpgrade(plan);
        setShowMpesaModal(true);
    };

    const handleGenerateCoupon = async () => {
        setGeneratingCoupon(true);
        setError(null);
        setCopied(false);
        try {
            const response = await apiFetch('/api/subscriptions/generate-coupon/', {
                method: 'POST'
            });
            if (response.success) {
                setCouponCode(response.coupon);
            } else {
                setError(response.error || 'Failed to generate coupon');
            }
        } catch (err) {
            console.error('[Subscription] Coupon error:', err);
            setError(err.message || 'Error generating coupon');
        } finally {
            setGeneratingCoupon(false);
        }
    };

    const handleCopy = async () => {
        if (!couponCode) return;
        try {
            await navigator.clipboard.writeText(couponCode);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    // Auto-open payment modal if ?auto=1 is present
    const [searchParams] = useSearchParams();
    const autoPay = searchParams.get('auto') === '1';
    const { selectedPlan } = useAuth();

    useEffect(() => {
        if (autoPay && !authLoading) {
            // Check if current tier matches the intended plan to avoid double-prompts
            const intendedBackendPlan = selectedPlan === 'standard' ? 'standard' : 'premium';
            const currentBackendPlan = currentTier === 'mentor_elite' ? 'standard' : (currentTier === 'scholar_vvip' ? 'premium' : 'free');

            if (intendedBackendPlan !== currentBackendPlan && (selectedPlan === 'standard' || selectedPlan === 'premium')) {
                handleUpgradeClick(selectedPlan);
            }
        }
    }, [autoPay, authLoading, selectedPlan, currentTier]);

    return (
        <div className="sub-premium-container">
            <div className="sub-hero-section">
                <div className="hero-decor-blur-1"></div>
                <div className="hero-decor-blur-2"></div>

                <header className="sub-hero-header">
                    <span className="sub-header-badge">
                        <Sparkles size={14} className="text-amber-400" />
                        AI-Powered Career Intelligence
                    </span>
                    <h1 style={{ marginTop: '20px' }} className="sub-hero-title">Choose Your Success Path</h1>
                    <p className="sub-hero-subtitle">
                        Unlock tailored academic roadmaps and professional mentoring
                        designed specifically for the Kenyan education system.
                    </p>
                </header>

                <div className="sub-trust-area">
                    <div className="sub-trust-section">
                        {/* Static items for desktop, marquee for mobile */}
                        <div className="trust-items-wrapper">
                            <div className="trust-item">
                                <div className="trust-icon-box mpesa">
                                    <MPesaIcon />
                                </div>
                                <div className="trust-text">
                                    <span className="trust-label">Safe M-Pesa Checkout</span>
                                    <span className="trust-sub">Instant Activation</span>
                                </div>
                            </div>
                            <div className="trust-item">
                                <div className="trust-icon-box blue">
                                    <ShieldCheck size={22} />
                                </div>
                                <div className="trust-text">
                                    <span className="trust-label">Cancel Anytime</span>
                                    <span className="trust-sub">No Commitment</span>
                                </div>
                            </div>
                            <div className="trust-item">
                                <div className="trust-icon-box amber">
                                    <Users size={22} />
                                </div>
                                <div className="trust-text">
                                    <span className="trust-label">24/7 Student Support</span>
                                    <span className="trust-sub">Dedicated Help</span>
                                </div>
                            </div>
                        </div>

                        {/* Duplicated for mobile marquee only */}
                        <div className="trust-items-wrapper mobile-only-marquee">
                            <div className="trust-item">
                                <div className="trust-icon-box mpesa">
                                    <MPesaIcon />
                                </div>
                                <div className="trust-text">
                                    <span className="trust-label">Safe M-Pesa Checkout</span>
                                    <span className="trust-sub">Instant Activation</span>
                                </div>
                            </div>
                            <div className="trust-item">
                                <div className="trust-icon-box blue">
                                    <ShieldCheck size={22} />
                                </div>
                                <div className="trust-text">
                                    <span className="trust-label">Cancel Anytime</span>
                                    <span className="trust-sub">No Commitment</span>
                                </div>
                            </div>
                            <div className="trust-item">
                                <div className="trust-icon-box amber">
                                    <Users size={22} />
                                </div>
                                <div className="trust-text">
                                    <span className="trust-label">24/7 Student Support</span>
                                    <span className="trust-sub">Dedicated Help</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Status Feedback */}
            {error && (
                <div className="sub-error-bar">
                    <X size={18} onClick={() => setError(null)} />
                    {error}
                </div>
            )}

            {pollingTxn && (
                <div className="sub-processing-overlay">
                    <div className="processing-card">
                        <div className="spinner-ultra"></div>
                        <h3>Awaiting Payment...</h3>
                        <p>Please check your phone for the M-Pesa prompt and enter your PIN.</p>
                        <span className="sub-text">Do not close this window.</span>
                    </div>
                </div>
            )}

            <div className="sub-pricing-grid-ultra">
                {/* Free Plan */}
                <div className={`pricing-card tier-free ${currentTier === 'explorer' ? 'active-plan' : ''}`}>
                    <div className="tier-badge">100% FREE</div>
                    <div className="card-top-inner">
                        <div className="tier-icon">
                            <Zap size={24} />
                        </div>
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
                        <li><Check size={18} /> Official KUCCPS program codes</li>
                        <li><Check size={18} /> Core institution discovery (public & private)</li>
                        <li><Check size={18} /> Standard email support (48-hour response)</li>
                    </ul>
                    <button
                        className={`path-btn secondary ${currentTier === 'explorer' ? 'current' : ''}`}
                        disabled={currentTier === 'explorer'}
                    >
                        {currentTier === 'explorer' ? 'Current Plan' : 'Select Plan'}
                    </button>
                </div>

                {/* Standard Plan - Primary */}
                <div className={`pricing-card tier-standard highlighted ${currentTier === 'mentor_elite' ? 'active-plan' : ''}`}>
                    <div className="tier-badge">80% OFF</div>
                    <div className="card-top-inner">
                        <div className="tier-icon primary">
                            <Sparkles size={28} className="animate-pulse" />
                        </div>
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
                    <button
                        className={`path-btn primary ${currentTier === 'mentor_elite' ? 'current' : ''}`}
                        onClick={() => handleUpgradeClick('standard')}
                        disabled={currentTier === 'mentor_elite' || upgrading === 'standard'}
                    >
                        {currentTier === 'mentor_elite' ? 'Current Plan' : upgrading === 'standard' ? 'Processing...' : 'Elevate Now'}
                        {(currentTier !== 'mentor_elite' && !upgrading) && <ArrowRight size={18} />}
                    </button>
                </div>

                {/* Premium Plan - Dominant */}
                <div className={`pricing-card tier-premium dominant ${currentTier === 'scholar_vvip' ? 'active-plan' : ''}`}>
                    <div className="tier-badge premium">79% OFF</div>
                    <div className="card-top-inner">
                        <div className="tier-icon superior">
                            <Crown size={32} />
                        </div>
                        <h3 className="plan-name">Scholar VVIP</h3>
                        <p className="plan-desc">The ultimate academic intelligence suite.</p>
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
                    <button
                        className={`path-btn premium ${currentTier === 'scholar_vvip' ? 'current' : ''}`}
                        onClick={() => handleUpgradeClick('premium')}
                        disabled={currentTier === 'scholar_vvip' || upgrading === 'premium'}
                    >
                        {currentTier === 'scholar_vvip' ? 'Current Plan' : upgrading === 'premium' ? 'Processing...' : 'Go VVIP'}
                        {(currentTier !== 'scholar_vvip' && !upgrading) && <Sparkles size={16} />}
                    </button>
                </div>
            </div>

            <div className="sub-sales-contact">
                <p>Want to talk to sales? <a href="tel:+254743720033">+254 743 720 033</a></p>
            </div>

            {/* M-Pesa Phone Modal */}
            {showMpesaModal && (
                <div className="mpesa-modal-backdrop" onClick={() => setShowMpesaModal(false)}>
                    <div className="mpesa-modal-content" onClick={(e) => e.stopPropagation()}>
                        <button className="modal-close" onClick={() => setShowMpesaModal(false)} aria-label="Close">
                            <X size={20} strokeWidth={2.5} />
                        </button>
                        <div className="mpesa-modal-header">
                            <MPesaIcon />
                            <h2>Checkout with M-Pesa</h2>
                            <p>Enter your M-Pesa number to receive the payment prompt.</p>
                        </div>
                        <div className="mpesa-input-group">
                            <label>M-Pesa Number</label>
                            <div className="phone-input-wrapper">
                                <Phone size={18} />
                                <input
                                    type="text"
                                    placeholder="e.g. 0712345678"
                                    value={phoneNumber}
                                    onChange={(e) => setPhoneNumber(e.target.value)}
                                    autoFocus
                                />
                            </div>
                            <span className="input-hint">Format: 07XXXXXXXX or 254XXXXXXXX</span>
                        </div>

                        <div className="mpesa-input-group">
                            <label>Coupon Code (Optional)</label>
                            <div className="phone-input-wrapper">
                                <Ticket size={18} />
                                <input
                                    type="text"
                                    placeholder="Enter coupon code"
                                    value={couponInput}
                                    onChange={(e) => setCouponInput(e.target.value)}
                                />
                            </div>
                            <span className="input-hint">Enter a code for a 10% discount</span>
                        </div>
                        <button
                            className="mpesa-pay-btn"
                            disabled={!phoneNumber || phoneNumber.length < 10}
                            onClick={initiateSTKPush}
                        >
                            <CreditCard size={18} />
                            Pay KES {selectedPlanForUpgrade === 'standard' ? '199' : '499'} Now
                        </button>
                        <p className="mpesa-secure-note">
                            <ShieldCheck size={14} /> Secure M-Pesa payment via PayHero
                        </p>
                    </div>
                </div>
            )}

            <div className="sub-referral-bottom-section">
                <div className="sub-referral-content">
                    <div className="sub-referral-text">
                        <h3>Invite Friends & Earn</h3>
                        <p>Share PROACTED with your fellow students and help them succeed.</p>
                    </div>

                    {!couponCode ? (
                        <button
                            className="sub-generate-btn-minimal"
                            onClick={handleGenerateCoupon}
                            disabled={generatingCoupon}
                        >
                            <Users size={18} />
                            {generatingCoupon ? 'Generating...' : 'Get Referral Code'}
                        </button>
                    ) : (
                        <div className="sub-coupon-banner-minimal">
                            <div className="coupon-code-wrapper-minimal">
                                <span className="coupon-label-minimal">Your Code:</span>
                                <strong className="coupon-code-minimal">{couponCode}</strong>
                                <button
                                    className={`sub-copy-btn-minimal ${copied ? 'copied' : ''}`}
                                    onClick={handleCopy}
                                    title="Copy to clipboard"
                                >
                                    {copied ? <CheckCircle2 size={14} /> : <Copy size={14} />}
                                    <span>{copied ? 'Copied!' : 'Copy'}</span>
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* VVIP Consent Modal */}
            {showVvipModal && (
                <div className="mpesa-modal-backdrop vvip-success-backdrop">
                    <div className="mpesa-modal-content vvip-success-card">
                        <div className="vvip-success-icon">
                            <Crown size={48} className="text-amber-400" />
                        </div>
                        <h2>Welcome to Scholar VVIP!</h2>
                        <p className="vvip-intro">
                            Your payment was successful. As a VVIP member, you have exclusive access
                            to our <strong>Diamond Support Group</strong>.
                        </p>

                        <div className="vvip-benefit-box">
                            <h4>What's included in this group:</h4>
                            <ul>
                                <li>Direct access to our application specialists</li>
                                <li>Real-time KUCCPS portal assistance</li>
                                <li>Early updates on university admission cycles</li>
                            </ul>
                        </div>

                        <div className="vvip-consent-query">
                            <p>Would you like to be added to this exclusive VVIP support group now?</p>
                            <div className="vvip-actions">
                                <button
                                    className="vvip-btn secondary"
                                    onClick={() => setShowVvipModal(false)}
                                >
                                    Not Now
                                </button>
                                <button
                                    className="vvip-btn primary"
                                    onClick={() => {
                                        setVvipStatus('consented');
                                        window.open('https://chat.whatsapp.com/BxnMLR9Hr1ACumLXac83dK', '_blank');
                                        setShowVvipModal(false);
                                    }}
                                >
                                    Yes, Add Me
                                </button>
                            </div>
                        </div>
                        <p className="vvip-disclaimer">
                            Note: We value your privacy. You will only be added if you consent here.
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
};
export default Subscription;
