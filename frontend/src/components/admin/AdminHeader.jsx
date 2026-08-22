import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { ChevronRight, LayoutDashboard, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import ThemeSwitcher from './ThemeSwitcher';
import { useAdminTheme } from '../../context/AdminThemeContext';

const AdminHeader = () => {
    const location = useLocation();
    const { isSidebarCollapsed, toggleSidebar } = useAdminTheme();
    const pathnames = location.pathname.split('/').filter(x => x);

    // Filter out 'admin' from breadcrumbs as it's the root
    const breadcrumbs = pathnames.filter(p => p !== 'admin');

    const formatLabel = (str) => {
        return str.charAt(0).toUpperCase() + str.slice(1).replace(/-/g, ' ');
    };

    return (
        <header className="admin-header" style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '1rem 2rem',
            background: 'var(--admin-bg-secondary)',
            borderBottom: '1px solid var(--admin-border-color)',
            position: 'sticky',
            top: 0,
            zIndex: 90,
            marginBottom: '1rem'
        }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                <button
                    onClick={toggleSidebar}
                    className="admin-btn-icon"
                    title={isSidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
                    style={{
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid var(--admin-border-color)',
                        color: 'var(--admin-text-muted)',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        padding: '8px',
                        borderRadius: '8px',
                        transition: 'all 0.2s ease'
                    }}
                >
                    {isSidebarCollapsed ? <PanelLeftOpen size={20} /> : <PanelLeftClose size={20} />}
                </button>

                <nav className="admin-breadcrumbs" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <Link to="/admin" style={{
                        color: 'var(--admin-text-muted)',
                        display: 'flex',
                        alignItems: 'center',
                        textDecoration: 'none'
                    }}>
                        <LayoutDashboard size={18} />
                    </Link>

                    {breadcrumbs.length > 0 && <ChevronRight size={16} style={{ color: 'var(--admin-text-muted)' }} />}

                    {breadcrumbs.map((name, index) => {
                        const routeTo = `/admin/${breadcrumbs.slice(0, index + 1).join('/')}`;
                        const isLast = index === breadcrumbs.length - 1;

                        return (
                            <React.Fragment key={name}>
                                {isLast ? (
                                    <span style={{
                                        color: 'var(--admin-text-primary)',
                                        fontWeight: 700,
                                        fontSize: '1rem'
                                    }}>
                                        {formatLabel(name)}
                                    </span>
                                ) : (
                                    <>
                                        <Link to={routeTo} style={{
                                            color: 'var(--admin-text-muted)',
                                            textDecoration: 'none',
                                            fontSize: '0.875rem'
                                        }}>
                                            {formatLabel(name)}
                                        </Link>
                                        <ChevronRight size={16} style={{ color: 'var(--admin-text-muted)' }} />
                                    </>
                                )}
                            </React.Fragment>
                        );
                    })}
                </nav>
            </div>

            <div className="admin-header-actions" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <ThemeSwitcher />
            </div>
        </header>
    );
};

export default AdminHeader;
