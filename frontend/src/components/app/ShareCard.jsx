import './ShareCard.css';

/**
 * ShareCard — Hidden DOM template rendered by html2canvas into a PNG image.
 * This component is NEVER visible to the user; it's positioned off-screen.
 * Fixed dimensions: 540px × 960px (renders at 2× scale = 1080×1920 story format).
 */
const ShareCard = ({ recommendations = [], cardRef }) => {
    // Rotating taglines — no emojis, pure text
    const taglines = [
        'AI found my perfect university path. Yours is next.',
        'My future, mapped by AI. Discover yours at KeDira.',
        'Stop guessing. Start knowing.',
        'My top 5 picks, chosen by AI — powered by KeDira.',
    ];
    const tagline = taglines[Math.floor(Math.random() * taglines.length)];

    const getFeasibility = (item) => {
        const studentPts = parseFloat(item.student_cluster_points || 0);
        const cutoffPts = parseFloat(item.prev_cutoff || item.cutoff_points || 0);
        const margin = studentPts - cutoffPts;

        if (margin > 5) return { label: 'Highly Likely', cls: 'feasibility-high' };
        if (margin >= 0 && margin <= 0.5) return { label: 'Competitive', cls: 'feasibility-mid' };
        if (margin < 0) return { label: 'Reach', cls: 'feasibility-reach' };
        return { label: 'Feasible', cls: 'feasibility-ok' };
    };

    return (
        <div className="share-card-root" ref={cardRef} aria-hidden="true">
            {/* Header */}
            <div className="sc-header">
                <div className="sc-logo-row">
                    <img
                        src="/favicon.png"
                        alt="KeDira"
                        className="sc-logo-img"
                        crossOrigin="anonymous"
                    />
                    <span className="sc-brand-name">KeDira</span>
                </div>
                <div className="sc-header-divider" />
                <h1 className="sc-headline">My AI-Powered University Roadmap</h1>
                <p className="sc-subheadline">Top 5 Course Recommendations</p>
            </div>

            {/* Recommendation Cards */}
            <div className="sc-cards">
                {recommendations.slice(0, 5).map((item, index) => {
                    const feasibility = getFeasibility(item);
                    return (
                        <div className="sc-card" key={index}>
                            <div className="sc-card-rank">#{item.rank || index + 1}</div>
                            <div className="sc-card-body">
                                <div className="sc-course-name">{item.course}</div>
                                <div className="sc-university">{item.university}</div>
                                {item.location && (
                                    <div className="sc-location">{item.location}</div>
                                )}
                            </div>
                            <div className={`sc-feasibility ${feasibility.cls}`}>
                                {feasibility.label}
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Footer */}
            <div className="sc-footer">
                <p className="sc-tagline">{tagline}</p>
                <div className="sc-url">proactedai.co.ke</div>
                <div className="sc-footer-bar" />
            </div>
        </div>
    );
};

export default ShareCard;
