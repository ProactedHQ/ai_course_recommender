import { useState, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import logo from "../assets/images/logos/logo.png";
import "./Navbar.css";

const Navbar = () => {
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [isScrolled, setIsScrolled] = useState(false);
    const { user } = useAuth();
    const navigate = useNavigate();
    const { pathname } = useLocation();

    // Close menu when route changes
    useEffect(() => {
        setIsMenuOpen(false);
    }, [pathname]);

    useEffect(() => {
        const handleScroll = () => {
            setIsScrolled(window.scrollY > 20);
        };
        window.addEventListener("scroll", handleScroll);
        return () => window.removeEventListener("scroll", handleScroll);
    }, []);

    const toggleMenu = () => setIsMenuOpen(!isMenuOpen);

    const handleNavClick = (e, id) => {
        e.preventDefault();
        const element = document.getElementById(id);
        if (element) {
            setIsMenuOpen(false);
            element.scrollIntoView({ behavior: "smooth" });
        } else {
            // If not on home page, navigate home first
            navigate(`/#${id}`);
            setTimeout(() => {
                const el = document.getElementById(id);
                if (el) el.scrollIntoView({ behavior: "smooth" });
            }, 100);
        }
    };

    return (
        <nav className={`navbar-outer ${isScrolled ? "scrolled" : ""}`}>
            <div className="section-inner navbar-inner">
                <div className="nav-logo" onClick={() => navigate("/")}>
                    <img src={logo} alt="KeDira Logo" className="logo-img" />
                    <span className="logo-text">KeDira <span className="logo-divider">|</span> PROACTEDAI</span>
                </div>

                <div className={`nav-links ${isMenuOpen ? "open" : ""}`}>
                    <Link to="/about">About</Link>
                    <Link to="/kedira-insider">Blog</Link>
                    <a href="#how-it-works" onClick={(e) => handleNavClick(e, "how-it-works")}>How It Works</a>
                    <a href="#benefits" onClick={(e) => handleNavClick(e, "benefits")}>Benefits</a>
                    <a href="#pricing" onClick={(e) => handleNavClick(e, "pricing")}>Pricing</a>
                    <a href="#faq" onClick={(e) => handleNavClick(e, "faq")}>FAQ</a>
                    <a href="#get-in-touch" onClick={(e) => handleNavClick(e, "get-in-touch")}>Contact</a>


                    <div className="nav-auth-mobile">
                        {user ? (
                            <button onClick={() => navigate("/app")}>Go to App</button>
                        ) : (
                            <>
                                <button className="secondary" onClick={() => navigate("/signin")}>Sign In</button>
                                <button onClick={() => navigate("/signup")}>Create Account</button>
                            </>
                        )}
                    </div>
                </div>

                <div className="nav-actions-desktop">
                    {user ? (
                        <button onClick={() => navigate("/app")}>Go to App</button>
                    ) : (
                        <>
                            <button className="secondary" onClick={() => navigate("/signin")}>Sign In</button>
                            <button onClick={() => navigate("/signup")}>Get Started</button>
                        </>
                    )}
                </div>

                <button
                    className={`hamburger ${isMenuOpen ? "active" : ""}`}
                    onClick={toggleMenu}
                    aria-label="Toggle menu"
                    aria-expanded={isMenuOpen}
                >
                    <span></span>
                    <span></span>
                    <span></span>
                </button>
            </div>
        </nav>
    );
};

export default Navbar;
