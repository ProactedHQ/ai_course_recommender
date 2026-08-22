import './SectionStats.css';

const SectionStats = () => {
    return (
        <section className="section-stats">
            <div className="stats-container">
                <div className="stats-wrapper">
                    <div className="stat-block">
                        <h3 className="stat-val">50k+</h3>
                        <p className="stat-txt">Students Helped</p>
                    </div>
                    <div className="stat-divider"></div>
                    <div className="stat-block">
                        <h3 className="stat-val">120+</h3>
                        <p className="stat-txt">Universities</p>
                    </div>
                    <div className="stat-divider"></div>
                    <div className="stat-block">
                        <h3 className="stat-val">90%</h3>
                        <p className="stat-txt">Placement Rate</p>
                    </div>
                </div>
            </div>
        </section>
    );
};

export default SectionStats;
