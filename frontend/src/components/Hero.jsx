import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import heroImage from "../assets/images/landing/home.png";
import "./Hero.css";

const phrases = [
    "AI-Powered Course Recommendations for KCSE Students",
    "KeDira: Your KCSE Success Roadmap",
    "KeDira: Clear Uni Direction, Zero Guesswork",
    "KeDira: The Ultimate KUCCPS Navigator",
    "KeDira: Secure Your Academic Future Today"
];

const Hero = () => {
    const { user, selectPlan } = useAuth();
    const navigate = useNavigate();

    const [currentPhraseIndex, setCurrentPhraseIndex] = useState(0);
    const [displayText, setDisplayText] = useState("");
    const [isDeleting, setIsDeleting] = useState(false);
    const [typingSpeed, setTypingSpeed] = useState(100);

    useEffect(() => {
        const handleTyping = () => {
            const currentFullPhrase = phrases[currentPhraseIndex];

            if (isDeleting) {
                setDisplayText(currentFullPhrase.substring(0, displayText.length - 1));
                setTypingSpeed(50);
            } else {
                setDisplayText(currentFullPhrase.substring(0, displayText.length + 1));
                setTypingSpeed(100);
            }

            if (!isDeleting && displayText === currentFullPhrase) {
                setTimeout(() => setIsDeleting(true), 2000);
            } else if (isDeleting && displayText === "") {
                setIsDeleting(false);
                setCurrentPhraseIndex((prev) => (prev + 1) % phrases.length);
            }
        };

        const timer = setTimeout(handleTyping, typingSpeed);
        return () => clearTimeout(timer);
    }, [displayText, isDeleting, currentPhraseIndex, typingSpeed]);

    const handleGetStarted = () => {
        if (user) {
            navigate("/onboarding");
        } else {
            selectPlan("free");
            navigate("/signup?plan=free&returnTo=/onboarding");
        }
    };

    const scrollToHowItWorks = (e) => {
        e.preventDefault();
        const element = document.getElementById("how-it-works");
        if (element) {
            element.scrollIntoView({ behavior: "smooth" });
        }
    };

    const renderTypedText = () => {
        if (displayText.startsWith("KeDira")) {
            return (
                <>
                    <span className="brand-highlight">KeDira</span>
                    {displayText.substring(6)}
                </>
            );
        }
        return displayText;
    };

    return (
        <section className="section-outer hero-section">
            <div className="section-inner hero-container">
                <div className="hero-content">
                    <h1 className="hero-title typewriter-container">
                        <span className="typewriter-text">{renderTypedText()}</span>
                        <span className="typewriter-cursor">|</span>
                    </h1>
                    <p className="hero-subtitle">
                        Get personalized university/TVET course suggestions based on your KCSE results, interests, and KUCCPS eligibility.
                    </p>

                    <div className="hero-actions">
                        <button className="primary" onClick={handleGetStarted}>
                            Get Started
                        </button>
                        <button className="secondary" onClick={scrollToHowItWorks}>
                            How It Works
                        </button>
                    </div>

                    <div className="micro-trust">
                        Explorer tier available • KUCCPS-aware matching • Takes 2–5 minutes
                    </div>
                </div>

                <div className="hero-visual">
                    <div className="hero-image-wrapper">
                        <img
                            src={heroImage}
                            alt="AI Course Recommendation Dashboard"
                            className="hero-image"
                            loading="eager"
                            width="600"
                            height="500"
                        />
                        <div className="hero-image-overlay" />
                    </div>
                </div>
            </div>
        </section>
    );
};

export default Hero;
