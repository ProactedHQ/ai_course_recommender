import { PenTool, Bot, Rocket } from "lucide-react";
import "./SectionHowItWorks.css";

const SectionHowItWorks = () => {
    const steps = [
        {
            number: "01",
            title: "Input Your Details",
            description: "Enter your KCSE grades, subjects, interests, and preferred institutions to build your profile.",
            icon: <PenTool size={24} />
        },
        {
            number: "02",
            title: "Receive AI Recommendations",
            description: "Our system matches your profile with KUCCPS requirements and current market trends.",
            icon: <Bot size={24} />
        },
        {
            number: "03",
            title: "Explore Your Path",
            description: "View eligible courses, understand why they match, and see your next registration steps.",
            icon: <Rocket size={24} />
        }
    ];

    return (
        <section className="section-outer how-it-works-section" id="how-it-works">
            <div className="section-inner">
                <h2 className="section-title">How KeDira Guides You</h2>
                <div className="section-title-accent" />
                <div className="steps-container">
                    {steps.map((step, index) => (
                        <div key={index} className="step-item">
                            <div className="step-header">
                                <span className="step-number">{step.number}</span>
                                <div className="step-line"></div>
                            </div>
                            <div className="step-content">
                                <div className="step-icon">
                                    {step.icon}
                                </div>
                                <h3 className="step-title">{step.title}</h3>
                                <p className="step-description">{step.description}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};


export default SectionHowItWorks;
