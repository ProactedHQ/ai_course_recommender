import React from "react";
import "./LegalLayout.css";
import Navbar from "../../components/Navbar";
import Footer from "../../components/Footer";

const CookiePolicy = () => {
    return (
        <div className="legal-page">
            <Navbar />
            <div className="legal-container">
                <section className="legal-hero-section">
                    <header className="legal-header">
                        <h1>Cookie Policy</h1>
                        <p className="last-updated">Last updated: 28 January 2026</p>
                    </header>
                </section>

                <div className="legal-content">
                    <section>
                        <h2>1. What Are Cookies?</h2>
                        <p>
                            Cookies are small text files stored on your device when you visit a website. They help the
                            platform function properly and provide a smoother user experience.
                        </p>
                    </section>

                    <section>
                        <h2>2. Cookies We Use</h2>
                        <p>We use a minimal set of cookies strictly for the following functional purposes:</p>
                        <ul>
                            <li><strong>Authentication & Session:</strong> To keep you signed in as you navigate between different pages.</li>
                            <li><strong>Security:</strong> To protect your account and prevent unauthorized access.</li>
                            <li><strong>Preferences:</strong> To remember your "Remember Me" choice for easier access on your next visit.</li>
                        </ul>
                    </section>

                    <section className="legal-contact-box">
                        <h2>3. What We Do NOT Use</h2>
                        <p>To ensure your privacy remains a priority, we guarantee that:</p>
                        <ul>
                            <li><strong>No Advertising Cookies:</strong> we do not use cookies to serve you ads or profiles.</li>
                            <li><strong>No Cross-Site Tracking:</strong> We do not track your activity on other websites.</li>
                            <li><strong>No Analytics Cookies:</strong> We do not use third-party analytics cookies to track your behavior at this time.</li>
                        </ul>
                    </section>

                    <section>
                        <h2>4. Managing Cookies</h2>
                        <p>
                            Most web browsers allow you to control cookies through their settings. You can choose to block
                            or delete cookies, but please note that doing so will sign you out and may prevent certain
                            features of KeDira from working as intended.
                        </p>
                    </section>

                    <section>
                        <h2>5. Third-Party Cookies</h2>
                        <p>
                            Our authentication is powered by <strong>Supabase</strong>. They may set necessary
                            functional cookies to manage your secure session.
                        </p>
                    </section>

                    <section>
                        <h2>6. Contact</h2>
                        <p>If you have any questions about our use of cookies, please contact our support team.</p>
                        <a
                            href="https://wa.me/254743720033?text=Hello%20Career%20Compass%20Support,%20I%20have%20a%20question%20about%20the%20Cookie%20Policy."
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

export default CookiePolicy;
