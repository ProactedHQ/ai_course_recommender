import React from "react";
import "./LegalLayout.css";
import Navbar from "../../components/Navbar";
import Footer from "../../components/Footer";

const LegalPrivacy = () => {
    return (
        <div className="legal-page">
            <Navbar />
            <div className="legal-container">
                <section className="legal-hero-section">
                    <header className="legal-header">
                        <h1>Privacy Policy</h1>
                        <p className="last-updated">Last updated: 28 January 2026</p>
                    </header>
                </section>

                <div className="legal-content">
                    <section>
                        <h2>1. Introduction</h2>
                        <p>
                            Welcome to <strong>KeDira</strong>, a platform developed by <strong>PROACTED</strong>.
                            We are committed to protecting the privacy of our students and users. This Privacy Policy explains
                            how we collect, use, and safeguard your data when you use our AI-driven course recommender.
                        </p>
                        <p>
                            This policy applies to all users of our web platform who seek guidance on career paths and course eligibility based on their academic and personal profiles.
                        </p>
                    </section>

                    <section>
                        <h2>2. Legal Basis</h2>
                        <p>
                            We process your personal data in accordance with the <strong>Kenya Data Protection Act, 2019</strong>.
                            All data processing is conducted lawfully, fairly, and transparently, with a focus on
                            enabling students to make informed decisions about their higher education.
                        </p>
                    </section>

                    <section>
                        <h2>3. Data We Collect</h2>
                        <p>To provide accurate recommendations, we collect the following information:</p>
                        <ul>
                            <li><strong>Account Data:</strong> Name and email address. If you choose to sign in with Google, we may collect your profile photo.</li>
                            <li><strong>Academic Inputs:</strong> KCSE subjects and grades.</li>
                            <li><strong>Personal Inputs:</strong> Your career interests, goals, and skills.</li>
                            <li><strong>Usage Data:</strong> Number of prompts used and timestamps of your interactions.</li>
                            <li><strong>Technical Data:</strong> Minimal information such as your IP address and browser type for security purposes.</li>
                        </ul>
                    </section>

                    <section>
                        <h2>4. How We Use Your Data</h2>
                        <p>The information we collect is used solely to:</p>
                        <ul>
                            <li>Generate personalized course and career recommendations.</li>s
                            <li>Improve the accuracy and logic of our AI recommendation system.</li>
                            <li>Manage your subscription status (Explorer, Mentor Elite, or Scholar VVIP).</li>
                            <li>Ensure the security of the platform and prevent fraudulent activity.</li>
                        </ul>
                    </section>

                    <section>
                        <h2>5. What We Do NOT Do</h2>
                        <p>Your trust is our priority. We explicitly commit to the following:</p>
                        <ul>
                            <li><strong>No Selling of Data:</strong> We do not sell your personal or academic information to third parties.</li>
                            <li><strong>No Unauthorized Sharing:</strong> We do not share your specific data with universities, KUCCPS, or any other third parties without your explicit consent.</li>
                            <li><strong>No Hidden Profiling:</strong> We do not use your data for automated decision-making that carries significant legal weight beyond providing guidance.</li>
                        </ul>
                    </section>

                    <section>
                        <h2>6. Data Storage & Security</h2>
                        <p>
                            Your data is stored on secure servers with strict access controls. We use encryption in transit
                            to ensure your information remains private. Access to your personal data is limited to a
                            redundantly small group of authorized developers solely for system maintenance and support.
                        </p>
                    </section>

                    <section>
                        <h2>7. Data Retention & Deletion</h2>
                        <p>
                            We retain your data only for as long as necessary to provide our services to you.
                            You have the right to request the deletion of your account and all associated data
                            at any time by contacting us.
                        </p>
                    </section>

                    <section>
                        <h2>8. Your Rights (Kenya DPA)</h2>
                        <p>As a data subject under the Kenya Data Protection Act, you have the following rights:</p>
                        <ul>
                            <li><strong>Right to Access:</strong> You can request a copy of the data we hold about you.</li>
                            <li><strong>Right to Correction:</strong> You can ask us to update or fix inaccurate information.</li>
                            <li><strong>Right to Deletion:</strong> You can request that we erase your personal data.</li>
                            <li><strong>Right to Object:</strong> You can object to how your data is being processed.</li>
                        </ul>
                    </section>

                    <section>
                        <h2>9. Children & Minors</h2>
                        <p>
                            KeDira is intended for students transitioning to higher education, typically aged 17 and above.
                            For students under 18, we encourage use with parental or guardian responsibility to ensure
                            privacy and guidance are maintained.
                        </p>
                    </section>

                    <section className="legal-contact-box">
                        <h2>10. Contact / Data Requests</h2>
                        <p>
                            If you have any questions about this policy or wish to exercise your rights to access,
                            correction, or deletion of your data, please contact our Student Support team directly.
                        </p>
                        <a
                            href="https://wa.me/254743720033?text=Hello%20Career%20Compass%20Support,%20I%20have%20a%20privacy/data%20request."
                            className="whatsapp-link"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            <span>Contact via WhatsApp Support</span>
                        </a>
                    </section>
                </div>
            </div>
            <Footer />
        </div>
    );
};

export default LegalPrivacy;
