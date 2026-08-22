import { NavLink, useNavigate } from 'react-router-dom';
import {
    LayoutDashboard,
    Users,
    CreditCard,
    Activity,
    BarChart3,
    ArrowLeft,
    LogOut,
    Shield,
    MessageSquare,
    ShieldAlert
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useAdminTheme } from '../../context/AdminThemeContext';
import '../../styles/AdminTheme.css';

const AdminSidebar = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const { isSidebarCollapsed } = useAdminTheme();

    const handleSignOut = async () => {
        try {
            await logout();
            navigate('/signin');
        } catch (error) {
            console.error('Sign out error:', error);
        }
    };

    const userDisplayName = user?.user_metadata?.full_name || user?.user_metadata?.name || user?.email || 'Admin';
    const userAvatar = user?.user_metadata?.avatar_url || user?.user_metadata?.picture;
    const initials = userDisplayName.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();

    const navItems = [
        { to: "/admin/dashboard", icon: LayoutDashboard, label: "Dashboard" },
        { to: "/admin/users", icon: Users, label: "User Management" },
        { to: "/admin/subscriptions", icon: CreditCard, label: "Subscriptions" },
        { to: "/admin/chats", icon: MessageSquare, label: "AI Chats" },
        { to: "/admin/activity", icon: Activity, label: "Activity Logs" },
        { to: "/admin/analytics", icon: BarChart3, label: "Analytics" },
        { to: "/admin/admins", icon: ShieldAlert, label: "Admins" },
    ];

    return (
        <aside className={`admin-sidebar ${isSidebarCollapsed ? 'collapsed' : ''}`}>
            <div className="admin-sidebar-header">
                <div className="admin-logo">
                    {userAvatar ? (
                        <img
                            src={userAvatar}
                            alt={userDisplayName}
                            className="admin-avatar-img"
                            referrerPolicy="no-referrer"
                            onError={(e) => {
                                e.target.style.display = 'none';
                                e.target.nextSibling.style.display = 'flex';
                            }}
                        />
                    ) : null}
                    <div className="admin-avatar-initials" style={{ display: userAvatar ? 'none' : 'flex' }}>
                        {initials}
                    </div>
                </div>
                {!isSidebarCollapsed && (
                    <div className="admin-user-info fade-in">
                        <div className="admin-sidebar-title">{userDisplayName}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--admin-text-muted)', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {user?.email}
                        </div>
                    </div>
                )}
            </div>

            <nav className="admin-nav">
                {navItems.map((item) => (
                    <NavLink
                        key={item.to}
                        to={item.to}
                        className="admin-nav-item"
                        title={isSidebarCollapsed ? item.label : ''}
                    >
                        <item.icon size={20} />
                        {!isSidebarCollapsed && <span className="fade-in">{item.label}</span>}
                    </NavLink>
                ))}
            </nav>

            <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <button
                    className="admin-btn admin-btn-danger"
                    onClick={handleSignOut}
                    style={{
                        width: '100%',
                        justifyContent: isSidebarCollapsed ? 'center' : 'center',
                        padding: isSidebarCollapsed ? '0.75rem 0' : '0.625rem 1.25rem'
                    }}
                    title={isSidebarCollapsed ? "Sign Out" : ""}
                >
                    <LogOut size={18} />
                    {!isSidebarCollapsed && <span className="fade-in">Sign Out</span>}
                </button>
            </div>
        </aside>
    );
};

export default AdminSidebar;
