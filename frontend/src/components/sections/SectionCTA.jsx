import { useNavigate } from "react-router-dom";
import { GraduationCap } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import "./SectionCTA.css";

const SectionCTA = () => {
    const { user } = useAuth();
    const navigate = useNavigate();

    const handleCTA = () => {
        if (user) {
            navigate("/onboarding");
        } else {
            navigate("/signup?returnTo=/onboarding");
        }
    };

    return (
        <section className="section-outer cta-bottom-section">
            <div className="section-inner">
                <div className="cta-card-premium">
                    <div className="cta-premium-content">
                        <div className="cta-icon-wrapper-premium">
                            <GraduationCap size={48} className="cta-premium-icon" />
                        </div>
                        <h2 className="cta-premium-title">Ready to Discover Your Ideal Career Path?</h2>
                        <p className="cta-premium-text">
                            Join thousands of students who have successfully navigated their course selection with KeDira.
                        </p>
                        <button className="cta-premium-btn" onClick={handleCTA}>
                            Get Started for Free
                        </button>
                    </div>
                </div>
            </div>
        </section>
    );
};


export default SectionCTA;
