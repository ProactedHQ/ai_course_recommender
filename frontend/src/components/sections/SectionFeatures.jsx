import { Tag, Puzzle, Scale, Diamond } from "lucide-react";
import "./SectionFeatures.css";

const SectionFeatures = () => {
    const benefits = [
        {
            title: "KCSE-Based Eligibility",
            description: "Recommendations reflect your exact grades and cluster points calculation.",
            icon: <Tag size={24} />
        },
        {
            title: "Personal Fit Analysis",
            description: "Your interests, strengths, and preferences inform the ranking logic.",
            icon: <Puzzle size={24} />
        },
        {
            title: "KUCCPS-Aware Logic",
            description: "Matches consider the latest KUCCPS guidelines and placement categories.",
            icon: <Scale size={24} />
        },
        {
            title: "Free & Premium Access",
            description: "Start free with basic matching; upgrade for deep analysis and unlimited use.",
            icon: <Diamond size={24} />
        }
    ];

    return (
        <section className="section-outer benefits-section" id="benefits">
            <div className="section-inner">
                <h2 className="section-title">Key Benefits of KeDira</h2>
                <div className="section-title-accent" />
                <div className="benefits-grid">
                    {benefits.map((benefit, index) => (
                        <div key={index} className="benefit-card">
                            <div className="benefit-icon">
                                {benefit.icon}
                            </div>
                            <h3 className="benefit-card-title">{benefit.title}</h3>
                            <p className="benefit-card-description">{benefit.description}</p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};


export default SectionFeatures;
