import { useEffect, useState } from 'react';
import { Users, UserCheck, CreditCard, TrendingUp, BarChart3, MessageSquare } from 'lucide-react';
import AdminStatsCard from '../../components/admin/AdminStatsCard';
import adminApi from '../../api/adminApi';
import '../../styles/AdminTheme.css';

const AdminDashboard = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadStats();
    }, []);

    const loadStats = async () => {
        try {
            setLoading(true);
            const data = await adminApi.getStats();
            setStats(data);
        } catch (err) {
            console.error('Failed to load stats:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div>
                <h1 style={{ marginBottom: '2rem', color: 'var(--admin-text-primary)' }}>Dashboard</h1>
                <p style={{ color: 'var(--admin-text-muted)' }}>Loading statistics...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div>
                <h1 style={{ marginBottom: '2rem', color: 'var(--admin-text-primary)' }}>Dashboard</h1>
                <div className="admin-card">
                    <p style={{ color: 'var(--admin-accent-danger)' }}>
                        Failed to load dashboard: {error}
                    </p>
                    <p style={{ color: 'var(--admin-text-muted)', marginTop: '1rem' }}>
                        Note: Backend API endpoints may not be implemented yet. This is a frontend-only interface.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="admin-dashboard-fade-in">
            <div style={{ marginBottom: '2.5rem' }}>
                <h1 style={{ marginBottom: '0.5rem', color: 'var(--admin-text-primary)', fontSize: '2rem', fontWeight: 800 }}>
                    Systems Overview
                </h1>
                <p style={{ color: 'var(--admin-text-muted)', fontSize: '1rem' }}>
                    Welcome back! Here's what's happening with KeDira today.
                </p>
            </div>

            <div className="admin-stats-grid">
                <AdminStatsCard
                    title="Total Users"
                    value={stats?.totalUsers || 0}
                    icon={Users}
                    trend={stats?.userGrowth || 12}
                    iconClass="primary"
                />

                <AdminStatsCard
                    title="Active Users"
                    value={stats?.activeUsers || 0}
                    icon={UserCheck}
                    trend={stats?.activeGrowth || 5}
                    iconClass="success"
                />

                <AdminStatsCard
                    title="Mentor Elite"
                    value={stats?.standardUsers || 0}
                    icon={CreditCard}
                    iconClass="primary"
                />

                <AdminStatsCard
                    title="Scholar VVIP"
                    value={stats?.premiumUsers || 0}
                    icon={TrendingUp}
                    iconClass="warning"
                />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem', marginTop: '1.5rem' }}>
                <div className="admin-card glass-premium">
                    <div className="admin-card-header">
                        <h2 className="admin-card-title">Quick Actions</h2>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
                        <button className="admin-btn admin-btn-secondary" style={{ justifyContent: 'flex-start' }} onClick={() => window.location.href = '/admin/users'}>
                            <Users size={18} /> Manage Users
                        </button>
                        <button className="admin-btn admin-btn-secondary" style={{ justifyContent: 'flex-start' }} onClick={() => window.location.href = '/admin/analytics'}>
                            <BarChart3 size={18} /> View Analytics
                        </button>
                        <button className="admin-btn admin-btn-secondary" style={{ justifyContent: 'flex-start' }} onClick={() => window.location.href = '/admin/subscriptions'}>
                            <CreditCard size={18} /> Billing Overview
                        </button>
                        <button className="admin-btn admin-btn-secondary" style={{ justifyContent: 'flex-start' }} onClick={() => window.location.href = '/admin/chats'}>
                            <MessageSquare size={18} /> Audit AI Chats
                        </button>
                    </div>
                </div>

                <div className="admin-card glass-premium">
                    <div className="admin-card-header">
                        <h2 className="admin-card-title">System Status</h2>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ color: 'var(--admin-text-secondary)' }}>API Backend</span>
                            <span className="admin-badge success">Operational</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ color: 'var(--admin-text-secondary)' }}>WebSocket (Redis)</span>
                            <span className="admin-badge success">Connected</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ color: 'var(--admin-text-secondary)' }}>AI Processing</span>
                            <span className="admin-badge success">Online</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AdminDashboard;
