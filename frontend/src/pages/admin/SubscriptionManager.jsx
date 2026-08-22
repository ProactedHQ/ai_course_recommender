import { useState, useEffect } from 'react';
import { CreditCard, TrendingUp, Users } from 'lucide-react';
import adminApi from '../../api/adminApi';
import AdminStatsCard from '../../components/admin/AdminStatsCard';
import SubscriptionBadge from '../../components/admin/SubscriptionBadge';
import AdminModal from '../../components/admin/AdminModal';
import { useAdminData } from '../../hooks/useAdminData';
import { useToast } from '../../context/ToastContext';
import '../../styles/AdminTheme.css';

const SubscriptionManager = () => {
    const { fetchData, loading: dataLoading } = useAdminData();
    const toast = useToast();
    const [stats, setStats] = useState(null);
    const [error, setError] = useState(null);
    const [isBulkModalOpen, setIsBulkModalOpen] = useState(false);
    const [bulkData, setBulkData] = useState({ ids: '', tier: 'explorer' });

    useEffect(() => {
        loadStats();
    }, []);

    const loadStats = async () => {
        try {
            const data = await fetchData('admin_stats', () => adminApi.getStats());
            setStats(data);
        } catch (err) {
            console.error('Failed to load stats:', err);
            setError(err.message);
            toast.error('Failed to sync subscription data.');
        }
    };

    const handleBulkUpdate = async () => {
        if (!bulkData.ids || !bulkData.tier) {
            toast.warning('Please provide both user IDs and a tier.');
            return;
        }

        try {
            const ids = bulkData.ids.split(',').map(id => id.trim());
            await adminApi.bulkUpdateSubscriptions(ids, bulkData.tier.toLowerCase());
            toast.success(`Successfully updated ${ids.length} subscriptions.`);
            setIsBulkModalOpen(false);
            setBulkData({ ids: '', tier: 'explorer' });
            loadStats();
        } catch (err) {
            console.error('Bulk update failed:', err);
            toast.error(`Bulk update failed: ${err.message}`);
        }
    };

    if (dataLoading && !stats) {
        return (
            <div className="admin-dashboard-fade-in">
                <h1 style={{ marginBottom: '2rem', color: 'var(--admin-text-primary)', fontFamily: 'var(--admin-font-heading)' }}>
                    Subscription Management
                </h1>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', color: 'var(--admin-text-muted)' }}>
                    <div className="admin-loading-spinner"></div>
                    <span>Synchronizing subscription metrics...</span>
                </div>
            </div>
        );
    }

    if (error && !stats) {
        return (
            <div className="admin-dashboard-fade-in">
                <h1 style={{ marginBottom: '2rem', color: 'var(--admin-text-primary)', fontFamily: 'var(--admin-font-heading)' }}>
                    Subscription Management
                </h1>
                <div className="admin-card" style={{ borderLeft: '4px solid var(--admin-accent-danger)' }}>
                    <p style={{ color: 'var(--admin-accent-danger)', fontWeight: 600 }}>Sync Failure</p>
                    <p style={{ color: 'var(--admin-text-muted)' }}>{error}</p>
                    <button className="admin-btn admin-btn-primary" style={{ marginTop: '1rem' }} onClick={loadStats}>
                        Retry Sync
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="admin-dashboard-fade-in">
            <h1 style={{ marginBottom: '2rem', color: 'var(--admin-text-primary)', fontFamily: 'var(--admin-font-heading)' }}>
                Subscription Management
            </h1>

            <div className="admin-stats-grid">
                <AdminStatsCard
                    title="Explorer Users"
                    value={stats?.freeUsers || 0}
                    icon={Users}
                    iconClass="primary"
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

            <div className="admin-card" style={{ marginBottom: '1.5rem' }}>
                <div className="admin-card-header">
                    <h2 className="admin-card-title">Bulk Operations</h2>
                </div>
                <p style={{ color: 'var(--admin-text-muted)', marginBottom: '1rem' }}>
                    Update subscription tiers for multiple users at once
                </p>
                <button
                    className="admin-btn admin-btn-primary"
                    onClick={() => setIsBulkModalOpen(true)}
                >
                    <CreditCard size={18} />
                    Bulk Update Subscriptions
                </button>
            </div>

            <AdminModal
                isOpen={isBulkModalOpen}
                onClose={() => setIsBulkModalOpen(false)}
                title="Bulk Subscription Update"
                footer={(
                    <>
                        <button className="admin-btn admin-btn-secondary" onClick={() => setIsBulkModalOpen(false)}>Cancel</button>
                        <button className="admin-btn admin-btn-primary" onClick={handleBulkUpdate}>Update Tiers</button>
                    </>
                )}
            >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    <div>
                        <label style={{ display: 'block', color: 'var(--admin-text-primary)', marginBottom: '0.5rem', fontSize: '0.875rem' }}>User IDs (Comma separated)</label>
                        <textarea
                            className="admin-search-input"
                            style={{ width: '100%', height: '100px', resize: 'none' }}
                            placeholder="e.g. 101, 102, 103"
                            value={bulkData.ids}
                            onChange={(e) => setBulkData({ ...bulkData, ids: e.target.value })}
                        />
                    </div>
                    <div>
                        <label style={{ display: 'block', color: 'var(--admin-text-primary)', marginBottom: '0.5rem', fontSize: '0.875rem' }}>New Subscription Tier</label>
                        <select
                            className="admin-search-input"
                            style={{ width: '100%' }}
                            value={bulkData.tier}
                            onChange={(e) => setBulkData({ ...bulkData, tier: e.target.value })}
                        >
                            <option value="explorer">Explorer</option>
                            <option value="mentor_elite">Mentor Elite</option>
                            <option value="scholar_vvip">Scholar VVIP</option>
                        </select>
                    </div>
                </div>
            </AdminModal>

            <div className="admin-card">
                <div className="admin-card-header">
                    <h2 className="admin-card-title">Subscription Distribution</h2>
                </div>
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                    gap: '1.5rem',
                    marginTop: '1rem'
                }}>
                    <div style={{
                        padding: '1.5rem',
                        background: 'var(--admin-bg-tertiary)',
                        borderRadius: '8px',
                        border: '1px solid var(--admin-border-color)'
                    }}>
                        <SubscriptionBadge tier="explorer" />
                        <div style={{
                            fontSize: '2rem',
                            fontWeight: 700,
                            marginTop: '0.5rem',
                            color: 'var(--admin-text-primary)'
                        }}>
                            {stats?.freeUsers || 0}
                        </div>
                        <div style={{ color: 'var(--admin-text-muted)', fontSize: '0.875rem' }}>
                            users
                        </div>
                    </div>

                    <div style={{
                        padding: '1.5rem',
                        background: 'var(--admin-bg-tertiary)',
                        borderRadius: '8px',
                        border: '1px solid var(--admin-border-color)'
                    }}>
                        <SubscriptionBadge tier="mentor_elite" />
                        <div style={{
                            fontSize: '2rem',
                            fontWeight: 700,
                            marginTop: '0.5rem',
                            color: 'var(--admin-text-primary)'
                        }}>
                            {stats?.standardUsers || 0}
                        </div>
                        <div style={{ color: 'var(--admin-text-muted)', fontSize: '0.875rem' }}>
                            users
                        </div>
                    </div>

                    <div style={{
                        padding: '1.5rem',
                        background: 'var(--admin-bg-tertiary)',
                        borderRadius: '8px',
                        border: '1px solid var(--admin-border-color)'
                    }}>
                        <SubscriptionBadge tier="scholar_vvip" />
                        <div style={{
                            fontSize: '2rem',
                            fontWeight: 700,
                            marginTop: '0.5rem',
                            color: 'var(--admin-text-primary)'
                        }}>
                            {stats?.premiumUsers || 0}
                        </div>
                        <div style={{ color: 'var(--admin-text-muted)', fontSize: '0.875rem' }}>
                            users
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SubscriptionManager;
