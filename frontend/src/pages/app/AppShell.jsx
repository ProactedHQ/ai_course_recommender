import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../../components/app/Sidebar';
import Topbar from '../../components/app/Topbar';
import ImpersonationBanner from '../../components/admin/ImpersonationBanner';
import './AppShell.css';

const AppShell = () => {
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

    const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);
    const closeSidebar = () => setIsSidebarOpen(false);

    const toggleCollapse = () => setIsSidebarCollapsed(!isSidebarCollapsed);

    return (
        <div className={`app-shell-container ${isSidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
            <ImpersonationBanner />

            {/* Mobile Topbar with Hamburger */}
            <Topbar onToggleSidebar={toggleSidebar} />

            <div className="app-layout">
                {/* Sidebar - fixed on desktop, drawer on mobile */}
                <Sidebar
                    isOpen={isSidebarOpen}
                    onClose={closeSidebar}
                    isCollapsed={isSidebarCollapsed}
                    onToggleCollapse={toggleCollapse}
                />

                {/* Main Content Area */}
                <main className={`app-main-panel ${isSidebarOpen ? 'sidebar-open' : ''} ${isSidebarCollapsed ? 'collapsed' : ''}`}>
                    <div className="app-content-wrapper">
                        <Outlet />
                    </div>
                </main>
            </div>

            {/* Mobile Sidebar Overlay */}
            {isSidebarOpen && (
                <div className="sidebar-overlay" onClick={closeSidebar} />
            )}
        </div>
    );
};

export default AppShell;
