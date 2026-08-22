import { useState } from "react";
import { Link } from "react-router-dom";
import WhatsAppConsentModal from "./common/WhatsAppConsentModal";
import "./Footer.css";

const Footer = () => {
    const [isModalOpen, setIsModalOpen] = useState(false);
    return (
        <footer className="footer-outer">
            <div className="section-inner footer-inner">
                <div className="footer-grid">
                    <div className="footer-brand">
                        <h3 className="logo-text">KeDira <span className="logo-divider">|</span> PROACTEDAI</h3>
                        <p className="brand-tagline">AI-powered course recommendations for a better future.</p>
                    </div>

                    <div className="footer-columns">
                        <div className="footer-col">
                            <h4>Product</h4>
                            <Link to="/about">About</Link>
                            <Link to="/kedira-insider">Blog</Link>
                            <Link to="/#benefits">Features</Link>
                            <Link to="/#pricing">Pricing</Link>
                            <Link to="/#how-it-works">How it Works</Link>
                        </div>

                        <div className="footer-col">
                            <h4>Legal</h4>
                            <Link to="/privacy-policy">Privacy Policy</Link>
                            <Link to="/terms-of-service">Terms of Service</Link>
                            <Link to="/cookie-policy">Cookie Policy</Link>
                        </div>


                        <div className="footer-col" id="footer-support">
                            <h4>Support</h4>
                            <Link to="/#faq">FAQ</Link>
                            <Link to="/#get-in-touch">Contact Us</Link>
                            <button
                                className="footer-link-btn"
                                onClick={() => setIsModalOpen(true)}
                            >
                                Technical Support
                            </button>
                            <WhatsAppConsentModal
                                isOpen={isModalOpen}
                                onClose={() => setIsModalOpen(false)}
                            />
                        </div>

                    </div>
                </div>

                <div className="footer-bottom">
                    <p>&copy; {new Date().getFullYear()} KeDira | PROACTEDAI. All rights reserved.</p>
                </div>
            </div>
        </footer>
    );
};

export default Footer;
