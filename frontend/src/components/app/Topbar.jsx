import React from 'react';
import { Menu } from 'lucide-react';
import logo from '../../assets/images/logos/logo.png';
import './Topbar.css';

const Topbar = ({ onToggleSidebar }) => {
    return (
        <header className="app-topbar">
            <button className="hamburger-btn" onClick={onToggleSidebar}>
                <Menu size={24} color="var(--color-primary)" />
            </button>
            <div className="topbar-logo">
                <img src={logo} alt="KeDira" className="topbar-logo-img" />
                <div className="logo-brand-container">
                    <span className="logo-name">KeDira</span>
                    <span className="logo-separator">|</span>
                    <span className="proacted-branding">PROACTEDAI</span>
                </div>
            </div>
            <div className="topbar-actions">
                {/* Future: notifications or help */}
            </div>
        </header>
    );
};

export default Topbar;
