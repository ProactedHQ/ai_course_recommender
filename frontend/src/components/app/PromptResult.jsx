import React, { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import {
    Sparkles, RefreshCcw, AlertCircle, MapPin, Building2,
    GraduationCap, ShieldCheck, Fingerprint, Target,
    Briefcase, Share, Loader2, Info
} from 'lucide-react';
import ShareCard from './ShareCard';
import ShareModal from './ShareModal';
import useShareRecommendations from '../../hooks/useShareRecommendations';
import './PromptResult.css';

/**
 * PromptResult Component — Enhanced with Premium Details
 */
const PromptResult = ({ result, onRestart }) => {
    const { cardRef, handleShare, isGenerating, imageBlob, imageUrl, showModal, closeModal } = useShareRecommendations();
    const location = useLocation();

    // 🚀 Auto-trigger share if coming from sidebar "Share" menu
    useEffect(() => {
        if (location.state?.autoShare && result && !isGenerating && !showModal) {
            // Short delay to ensure DOM is ready for snapshot
            const timer = setTimeout(() => {
                handleShare();
            }, 600);
            return () => clearTimeout(timer);
        }
    }, [location.state, result, handleShare]);

    // 1. Connectivity/Empty State
    if (!result) {
        return (
            <div className="result-container text-center py-20">
                <div className="result-error bg-red-50/50 p-12 rounded-none border border-red-100 backdrop-blur-sm">
                    <AlertCircle size={64} className="text-red-400 mx-auto mb-6" />
                    <h3 className="text-2xl font-black text-slate-900 mb-3">No Results Found</h3>
                    <p className="text-slate-500 mb-8 max-w-sm mx-auto font-medium">We couldn't generate recommendations at this time. This might be due to a temporary connectivity issue.</p>
                    <button className="premium-restart-btn mx-auto" onClick={onRestart}>
                        <RefreshCcw size={20} />
                        <span>Try Another Search</span>
                    </button>
                </div>
            </div>
        );
    }

    const recBlock = result.recommendations || result;
    const recommendations = recBlock.top_5;
    const pathUsed = recBlock.path_used || result.path_used || 'unknown';
    const submissionId = recBlock.submission_id || result.submission_id || 'N/A';

    if (!recommendations || !Array.isArray(recommendations)) {
        return (
            <div className="result-container text-center py-20">
                <div className="result-error bg-amber-50/50 p-12 rounded-none border border-amber-100 backdrop-blur-sm">
                    <AlertCircle size={64} className="text-amber-400 mx-auto mb-6" />
                    <h3 className="text-2xl font-black text-slate-900 mb-3">Data Refinement Needed</h3>
                    <p className="text-slate-500 mb-8 max-w-sm mx-auto font-medium">The analytical engine returned a non-standard response. Please check your inputs and try again.</p>
                    <button className="premium-restart-btn mx-auto" onClick={onRestart}>
                        <RefreshCcw size={20} />
                        <span>Re-Initialize Search</span>
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="result-container">
            {/* Metadata bar removed for cleaner UI as requested */}

            <div className="result-header">

                <div style={{ alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px' }}>
                    <div>
                        <h2 className="result-title">Academic Pathway Intel</h2>
                        <p className="result-subtitle">Our AI has analyzed thousands of data points to identify your optimal university trajectory.</p>
                        
                        {/* ── KUCCPS Performance Index Disclaimer ───────────────────── */}
                        <div className="pi-disclaimer-banner" style={{ marginTop: '1.5rem', marginBottom: '0.5rem' }}>
                            <div className="pi-disclaimer-icon">
                                <Info size={16} />
                            </div>
                            <div className="pi-disclaimer-content">
                                <p className="pi-disclaimer-title" style={{ fontSize: '0.7rem' }}>KUCCPS Entry Disclosure</p>
                                <p className="pi-disclaimer-text" style={{ fontSize: '0.8rem', lineHieght: '1.4' }}>
                                    Points here use standard KCSE formulas. KUCCPS uses <strong>internal Performance Indices (PI)</strong> from KNEC
                                    that are <strong>not publicly available</strong>. Expect small discrepancies vs. your official{' '}
                                    <a href="https://students.kuccps.net" target="_blank" rel="noopener noreferrer" className="pi-disclaimer-link">KUCCPS Portal</a>.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

            </div>
            {/* Share Button */}
            <div style={{ position: 'relative', flexShrink: 0, marginLeft: '0px', padding: '10px' }} className="share-btn-wrapper">
                <button
                    className="share-result-btn"
                    onClick={handleShare}
                    disabled={isGenerating}
                    aria-label="Share your recommendations"
                    title="Share to WhatsApp, Instagram, Facebook or X"
                >
                    {isGenerating
                        ? <Loader2 size={16} className="share-btn-spinner" />
                        : <Share size={16} />}
                    <span>Share</span>
                </button>
            </div>
            {/* Hidden ShareCard — rendered off-screen for html2canvas */}
            <ShareCard recommendations={recommendations} cardRef={cardRef} />

            {/* Share Modal */}
            {showModal && imageBlob && (
                <ShareModal
                    imageUrl={imageUrl}
                    imageBlob={imageBlob}
                    onClose={closeModal}
                />
            )}

            {/* Scholar VVIP: Qualified Clusters & Points */}
            {recBlock.cluster_summary && (
                <div className="premium-clusters-section">
                    <div className="section-header">
                        <Target size={24} className="text-teal-600" />
                        <h3 className="text-xl font-black text-slate-800">Your Qualified Academic Clusters</h3>
                    </div>
                    <p className="section-subtitle">Based on your KCSE results, here are all the academic clusters you qualify for and your calculated points.</p>
                    <div className="clusters-grid">
                        {recBlock.cluster_summary.map((cls, idx) => (
                            <div key={idx} className="cluster-item-card">
                                <span className="cluster-name">{cls.name}</span>
                                <span className="cluster-points">{cls.points.toFixed(3)}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <div className="recommendations-list">
                {recommendations.length > 0 ? recommendations.map((item, index) => {
                    const insightText = (item.insight || '').trim() || 'Personalized insight unavailable for this recommendation.';
                    const isFallback = item.source === 'fallback' || pathUsed === 'fallback';

                    // Feasibility Logic
                    const studentPts = parseFloat(item.student_cluster_points || 0);
                    const cutoffPts = parseFloat(item.prev_cutoff || 0);
                    const margin = studentPts - cutoffPts;
                    let feasibility = { label: 'Feasible', color: 'text-emerald-600', bg: 'bg-emerald-50' };

                    if (margin < 0.5 && margin >= 0) {
                        feasibility = { label: 'Competitive', color: 'text-amber-600', bg: 'bg-amber-50' };
                    } else if (margin < 0) {
                        feasibility = { label: 'Reach', color: 'text-rose-600', bg: 'bg-rose-50' };
                    } else if (margin > 5) {
                        feasibility = { label: 'Highly Likely', color: 'text-teal-600', bg: 'bg-teal-50' };
                    }

                    return (
                        <div className="course-card-premium is-expanded" key={index}>
                            <div className="course-card-header-premium">
                                <div className="flex justify-between items-start mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className="rank-badge">
                                            #{item.rank || index + 1}
                                        </div>
                                        <div className={`feasibility-tag ${feasibility.bg} ${feasibility.color}`}>
                                            <ShieldCheck size={12} />
                                            <span>{feasibility.label}</span>
                                        </div>
                                    </div>

                                    <div className="flex gap-2">
                                        {item.public_private && (
                                            <div className="metadata-badge type-badge-premium">
                                                <ShieldCheck size={11} className="" />
                                                <span>{item.public_private === 'PUBLIC_UNIVERSITY' ? 'Public' : 'Private'}</span>
                                            </div>
                                        )}
                                        {item.level && (
                                            <div className="metadata-badge level-badge-premium">
                                                <GraduationCap size={11} className="" />
                                                <span>{item.level}</span>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <div className="cluster-header-premium">
                                    {item.cluster || 'Academic Trajectory'}
                                </div>

                                <div className="flex justify-between items-start">
                                    <h3 className="course-title-premium">{item.course}</h3>
                                    {item.programme_code && (
                                        <div className="code-badge-premium">
                                            <Fingerprint size={12} className="text-blue-500" />
                                            <span className="label">Programme Code:</span>
                                            <span className="value">{item.programme_code}</span>
                                        </div>
                                    )}
                                </div>

                                <div className="institution-row-premium">
                                    <Building2 size={18} className="text-slate-400" />
                                    <span className="institution-name-premium">{item.university}</span>
                                </div>

                                <div className="flex flex-wrap items-center gap-x-4 gap-y-2 mt-4 pb-4 border-b border-slate-100">
                                    {item.location && (
                                        <div className="location-row-premium">
                                            <MapPin size={14} className="text-teal-500" />
                                            <span>{item.location}</span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            <div className="course-card-body-premium">
                                <div className="technical-grid-premium">
                                    <div className="tech-item">
                                        <span className="tech-label">Your Cluster Points</span>
                                        <div className="flex items-center gap-1">
                                            <span className="tech-value highlight">{item.student_cluster_points || 'N/A'}</span>
                                            <Target size={12} className="text-teal-500" />
                                        </div>
                                    </div>

                                    <div className="tech-item">
                                        <span className="tech-label">Admission Cutoff ({item.cutoff_year})</span>
                                        <span className="tech-value text-slate-700">{item.cutoff_points || item.prev_cutoff || 'N/A'}</span>
                                    </div>


                                    {item.prev_cutoff && item.cutoff_points && (
                                        <div className="tech-item">
                                            <span className="tech-label">Prev. Cutoff ({item.prev_cutoff_year || 'Historical'})</span>
                                            <span className="tech-value text-slate-500 font-medium">{item.prev_cutoff}</span>
                                        </div>
                                    )}

                                    {(!item.prev_cutoff || !item.cutoff_points) && (
                                        <div className="tech-item">
                                            <span className="tech-label">Feasibility Margin</span>
                                            <span className={`tech - value ${margin >= 0 ? 'text-emerald-600' : 'text-rose-600'} `}>
                                                {margin >= 0 ? '+' : ''}{margin.toFixed(3)}
                                            </span>
                                        </div>
                                    )}
                                </div>

                                <div className="analysis-box-premium">
                                    <div className="box-header-premium">
                                        <Sparkles size={14} className="text-purple-600" />
                                        <h4>{isFallback ? 'Eligibility Analysis' : 'AI Personalized Insight'}</h4>
                                    </div>
                                    <p className="analysis-text-premium">
                                        {insightText}
                                    </p>
                                </div>

                                {/* Detailed Content - Always Visible */}
                                <div className="expanded-premium-content border-t border-slate-100 pt-4 mt-2">
                                    {item.career_preview && (
                                        <div className="premium-subsection">
                                            <div className="subsection-header">
                                                <Briefcase size={16} />
                                                <h5>Career Outlook</h5>
                                            </div>
                                            <p className="subsection-text">{item.career_preview}</p>
                                        </div>
                                    )}

                                    {item.action_plan && (
                                        <div className="premium-subsection">
                                            <div className="subsection-header">
                                                <Target size={16} />
                                                <h5>Your Action Plan</h5>
                                            </div>
                                            <div className="action-plan-content">
                                                {typeof item.action_plan === 'string' ? (
                                                    <p className="subsection-text">{item.action_plan}</p>
                                                ) : Array.isArray(item.action_plan) ? (
                                                    <ul className="action-steps-list">
                                                        {item.action_plan.map((step, sIdx) => (
                                                            <li key={sIdx}>{step}</li>
                                                        ))}
                                                    </ul>
                                                ) : null}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    );
                }) : (
                    <div className="empty-result text-center py-12 bg-slate-50 rounded-none border border-dashed border-slate-200">
                        <p className="text-slate-400 font-bold">No pathways currently match your profile configuration.</p>
                    </div>
                )}
            </div>

            <div className="conversational-footer">
                <div className="footer-content">
                    <Sparkles className="sparkle-icon" size={32} />
                    <div className="footer-text">
                        <h4>Explore Alternative Trajectories</h4>
                        <p>Adjust your academic parameters or priority weights to discover other high-performance paths.</p>
                    </div>
                </div>
                <button className="premium-restart-btn" onClick={onRestart}>
                    <RefreshCcw size={20} />
                    <span>Re-Initialize Search</span>
                </button>
            </div>
        </div>
    );
};

export default PromptResult;
