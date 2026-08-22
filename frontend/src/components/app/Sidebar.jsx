import { NavLink, useNavigate } from 'react-router-dom';
import {
    PlusCircle, Compass, Settings, CreditCard,
    LogOut, Shield, ChevronsLeft, ChevronsRight
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { usePromptHistory } from '../../hooks/usePromptHistory';
import PlanBadge from './PlanBadge';
import PromptHistoryList from './PromptHistoryList';
import logo from '../../assets/images/logos/logo.png';
import './Sidebar.css';

const Sidebar = ({ isOpen, onClose, isCollapsed, onToggleCollapse }) => {
    const { user, logout, selectedPlan, userRole } = useAuth();
    const { history, loading } = usePromptHistory();
    const navigate = useNavigate();

    const handleSignOut = async () => {
        try {
            await logout();
            navigate('/signin');
        } catch (error) {
            console.error('Sign out error:', error);
        }
    };

    const userDisplayName = user?.user_metadata?.full_name || user?.user_metadata?.name || user?.email || 'Student';
    const userAvatar = user?.user_metadata?.avatar_url || user?.user_metadata?.picture;
    const initials = userDisplayName.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();

    // Backend-verified admin check
    const isStaff = userRole?.is_staff === true && userRole?.is_student === false;

    return (
        <aside className={`app-sidebar ${isOpen ? 'open' : ''} ${isCollapsed ? 'collapsed' : ''}`}>
            <div className="sidebar-identity-section">
                <div className="sidebar-header">
                    <div className="sidebar-logo" onClick={() => { navigate('/app/new'); if (onClose) onClose(); }}>
                        <img src={logo} alt="KeDira" className="sidebar-logo-img" />
                        <div className="logo-brand-container">
                            <span className="logo-name">KeDira</span>
                            <span className="logo-separator">|</span>
                            <span className="proacted-branding">PROACTEDAI</span>
                        </div>
                    </div>

                    {/* Premium Collapse Toggle (Visible on Desktop) */}
                    <button className="sidebar-collapse-toggle" onClick={onToggleCollapse}>
                        {isCollapsed ? <ChevronsRight size={18} /> : <ChevronsLeft size={18} />}
                    </button>
                </div>

                <div className="sidebar-user-card">
                    <div className="user-info-row">
                        <div className="avatar-wrapper">
                            {userAvatar ? (
                                <img
                                    src={userAvatar}
                                    alt={userDisplayName}
                                    className="user-avatar"
                                    referrerPolicy="no-referrer"
                                    onError={(e) => {
                                        e.target.style.display = 'none';
                                        e.target.nextSibling.style.display = 'flex';
                                    }}
                                />
                            ) : null}
                            <div className="user-initials" style={{ display: userAvatar ? 'none' : 'flex' }}>
                                {initials}
                            </div>
                        </div>

                        {!isCollapsed && (
                            <div className="user-identity">
                                <span className="user-name">{userDisplayName}</span>
                                <span className="user-email">{user?.email}</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <nav className="sidebar-nav">
                <div className="nav-group">
                    {!isCollapsed && <small className="nav-group-label">Tools</small>}
                    <NavLink to="/app/new" className="nav-item" title="New Recommendation" onClick={onClose}>
                        <PlusCircle size={18} /> {!isCollapsed && <span>New Recommendation</span>}
                    </NavLink>
                </div>

                <div className="nav-group history-group">
                    {!isCollapsed && <small className="nav-group-label">History</small>}
                    <PromptHistoryList history={history} loading={loading} onClose={onClose} isCollapsed={isCollapsed} />
                </div>

                <div className="nav-group mt-auto">
                    <NavLink to="/app/settings" className="nav-item" title="Settings" onClick={onClose}>
                        <Settings size={18} /> {!isCollapsed && <span>Settings</span>}
                    </NavLink>

                    <NavLink to="/app/subscription" className="nav-item subscription-link" title="Subscription" onClick={onClose}>
                        <CreditCard size={18} />
                        {!isCollapsed && (
                            <div className="sub-nav-content">
                                <span>Subscription</span>
                                <div className={`sub-status-pill ${selectedPlan}`}>
                                    {(() => {
                                        const plan = selectedPlan?.toLowerCase();
                                        if (plan === 'explorer' || plan === 'free') return 'Explorer';
                                        if (plan === 'standard' || plan === 'mentor_elite') return 'Mentor Elite';
                                        if (plan === 'premium' || plan === 'scholar_vvip') return 'Scholar VVIP';
                                        return 'Explorer';
                                    })()}
                                </div>
                            </div>
                        )}
                    </NavLink>

                    {/* Admin Panel — only visible to staff (backend-verified) */}
                    {isStaff && (
                        <NavLink to="/admin" className="nav-item admin-link" title="Admin Panel" onClick={onClose}>
                            <Shield size={18} /> {!isCollapsed && <span>Admin Panel</span>}
                        </NavLink>
                    )}
                </div>
            </nav>

            <div className="sidebar-footer">
                <button className="signout-btn" title="Sign Out" onClick={handleSignOut}>
                    <LogOut size={18} /> {!isCollapsed && <span>Sign Out</span>}
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;
