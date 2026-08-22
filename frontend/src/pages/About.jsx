import React from "react";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import { Linkedin, FlaskConical, Target, ShieldCheck, Users } from "lucide-react";
import "./About.css";

const About = () => {
    const team = [
        {
            name: "Cynthia Amol",
            role: "Academic Supervisor / ML Researcher",
            tagline: "PhD Candidate • Google NLP Fellow",
            linkedin: "https://www.linkedin.com/in/cynthia-amol/"
        },
        {
            name: "Benaiah Galavu",
            role: "Computer Scientist",
            linkedin: "#"
        },
        {
            name: "Mercy Okeyo",
            role: "Computer Scientist",
            linkedin: "https://www.linkedin.com/in/mercy-achieng-283294255/"
        },
        {
            name: "Simon Muthungu",
            role: "Computer Scientist",
            linkedin: "https://www.linkedin.com/in/simon-muthungu-b149821b6/"
        },
        {
            name: "Vitalis Amakalu",
            role: "Software Engineer / Computer Scientist",
            tagline: "ALX Software Engineering Alumnus (Cohort 22) • 'I Do Hard Things'",
            linkedin: "https://www.linkedin.com/in/amakaluvitalis/"
        }

    ];

    return (
        <div className="about-page">
            <Navbar />
            <div className="about-container">
                <section className="about-hero-section">
                    <div className="hero-overlay"></div>
                    <div className="hero-content">
                        <h1>A Proactive Approach to Education</h1>
                        <p className="about-lead">
                            Bridging the gap between KCSE results and university admission through evidence-based AI guidance.
                        </p>
                    </div>
                </section>

                <section className="about-section why-section">
                    <div className="research-intro">
                        <h2>Why PROACTED Exists</h2>
                        <p>
                            Every year, thousands of students in Sub-Saharan Africa transition from secondary to higher education with inadequate guidance.
                            Decisions are often made under pressure, without a clear understanding of eligibility or long-term career suitability.
                            This lack of informed choice contributes to low completion rates and professional misalignment.
                        </p>
                        <p>
                            PROACTED was born from a need for systemic change—moving from reactive academic support to proactive intervention.
                        </p>
                    </div>
                </section>

                <section className="about-section">
                    <h2><FlaskConical size={32} /> The Research Foundation</h2>
                    <p>
                        This platform is grounded in peer-reviewed academic research conducted at <strong>Maseno University</strong>,
                        where Education Data Mining (EDM) and Machine Learning techniques were used to study how academic performance
                        and student interests influence course suitability and completion outcomes.
                    </p>

                    <p>
                        In the original research, Sentence-BERT (SBERT) was used for semantic interest matching, while Logistic Regression
                        was applied to model performance-based eligibility. These baseline models achieved strong empirical results:
                    </p>

                    <div className="research-stats">
                        <div className="stat-card">
                            <span className="stat-value">0.96</span>
                            <span className="stat-label">SBERT Matching Accuracy</span>
                        </div>
                        <div className="stat-card">
                            <span className="stat-value">0.97</span>
                            <span className="stat-label">Performance Model Accuracy</span>
                        </div>
                    </div>

                    <p>
                        These results validated the feasibility of a data-driven, proactive approach to course guidance.
                        However, it is important to note that the production platform goes beyond the research prototypes.
                    </p>

                    <p>
                        The live PROACTED system incorporates refined and enhanced models, improved data representation,
                        and practical decision-layer logic designed specifically for real-world student use. These improvements
                        focus not only on statistical accuracy, but also on clarity, relevance, usability, and student experience—factors
                        that cannot be fully captured in academic experiments alone.
                    </p>

                    <p>
                        The research provides the scientific foundation; the platform delivers the practical, student-ready evolution of that work.
                    </p>
                </section>

                <section className="about-section">
                    <h2><Target size={32} /> Why Proactive Selection?</h2>
                    <p>
                        The complete PROACTED model includes performance monitoring and educator interventions. However, for this initial release,
                        we have focused exclusively on <strong>Proactive Course Recommendation</strong>.
                    </p>
                    <div className="current-scope">
                        <p><strong>Impact Focus:</strong> Poor course selection is the earliest and most significant academic risk.
                            By addressing this at the root, we empower students before they enter a system they are not suited for.</p>
                    </div>
                    <p>
                        This platform identifies ideal paths for <strong>KCSE (8-4-4)</strong> students by analyzing academic performance,
                        personal interests, and career priorities in a single, unified engine.
                    </p>
                </section>

                <section className="about-section">
                    <h2><ShieldCheck size={32} /> Ethical Alignment</h2>
                    <p>
                        We adhere to strict ethical AI principles. This means complete transparency in how recommendations are generated,
                        absolute student data privacy, and a commitment to never selling student information to third parties.
                        Our goal is to assist decision-making, not to automate it without human context.
                    </p>
                </section>

                <section className="about-section">
                    <h2><Users size={32} /> The People Behind the Work</h2>
                    <div className="team-grid">
                        {team.map((member, idx) => (
                            <div key={idx} className="team-card">
                                <span className="team-name">{member.name}</span>
                                <span className="team-role">{member.role}</span>
                                {member.tagline && <span className="team-tagline">{member.tagline}</span>}
                                {member.linkedin !== "#" && (
                                    <a href={member.linkedin} target="_blank" rel="noopener noreferrer" className="linkedin-link">
                                        <Linkedin size={16} />
                                        <span>View Profile</span>
                                    </a>
                                )}
                            </div>
                        ))}
                    </div>
                </section>

                <section className="vision-box">
                    <h2>Impact for 2025/2026</h2>
                    <p>
                        The 2025 Kenya Certificate of Secondary Education (KCSE) results revealed that out of <strong>993,226 candidates</strong>,
                        only <strong>27.18% (270,715)</strong> achieved a C+ or above. With <strong>634,082 students</strong> receiving a pass grade (D+ and above),
                        the need for accurate, proactive career guidance has never been more critical.
                    </p>
                    <p>
                        As one of the final cohorts under the 8-4-4 system, these students are at a significant milestone.
                        Our goal is to ensure that every one of these individuals touches KeDira as they start their next journey,
                        finding the right direction through data-driven insights.
                    </p>
                </section>
            </div>
            <Footer />
        </div>
    );
};

export default About;
