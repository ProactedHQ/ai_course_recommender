import { useState, useEffect } from 'react';
import { TrendingUp, Users, UserCheck, CreditCard, BarChart3, PieChart, Activity } from 'lucide-react';
import adminApi from '../../api/adminApi';
import AdminStatsCard from '../../components/admin/AdminStatsCard';
import AdminChart from '../../components/admin/AdminChart';
import { useAdminData } from '../../hooks/useAdminData';
import '../../styles/AdminTheme.css';

const Analytics = () => {
    const { fetchData, loading: dataLoading } = useAdminData();
    const [analytics, setAnalytics] = useState(null);
    const [period, setPeriod] = useState('30d');
    const [error, setError] = useState(null);

    useEffect(() => {
        loadAnalytics();
    }, [period]);

    const loadAnalytics = async () => {
        try {
            const data = await fetchData(`analytics_${period}`, () => adminApi.getAnalytics(period));
            setAnalytics(data);
        } catch (err) {
            setError(err.message);
        }
    };

    const userGrowthData = analytics?.growthData || [
        { label: 'Jan', value: 0 },
        { label: 'Feb', value: 0 },
        { label: 'Mar', value: 0 },
        { label: 'Apr', value: 0 },
        { label: 'May', value: 0 },
        { label: 'Jun', value: 0 },
        { label: 'Jul', value: 0 },
    ];

    const subDistributionData = [
        { label: 'Explorer', value: analytics?.freeUsers || 0 },
        { label: 'Mentor', value: analytics?.standardUsers || 0 },
        { label: 'Scholar', value: analytics?.premiumUsers || 0 },
    ];

    if (dataLoading && !analytics) {
        return (
            <div className="admin-dashboard-fade-in">
                <h1 style={{ marginBottom: '2rem', color: 'var(--admin-text-primary)', fontFamily: 'var(--admin-font-heading)' }}>
                    Analytics Center
                </h1>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', color: 'var(--admin-text-muted)' }}>
                    <div className="admin-loading-spinner"></div>
                    <span>Synchronizing real-time analytics...</span>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div>
                <h1 style={{ marginBottom: '2rem', color: 'var(--admin-text-primary)' }}>
                    Analytics
                </h1>
                <div className="admin-card">
                    <p style={{ color: 'var(--admin-accent-danger)' }}>
                        Failed to load analytics: {error}
                    </p>
                    <p style={{ color: 'var(--admin-text-muted)', marginTop: '1rem' }}>
                        Note: Backend API endpoints may not be implemented yet. This is a frontend-only interface.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div>
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '2rem'
            }}>
                <h1 style={{ color: 'var(--admin-text-primary)', margin: 0 }}>
                    Analytics
                </h1>
                <select
                    className="admin-search-input"
                    value={period}
                    onChange={(e) => setPeriod(e.target.value)}
                    style={{ minWidth: '150px' }}
                >
                    <option value="7d">Last 7 Days</option>
                    <option value="30d">Last 30 Days</option>
                    <option value="90d">Last 90 Days</option>
                    <option value="1y">Last Year</option>
                </select>
            </div>

            <div className="admin-stats-grid">
                <AdminStatsCard
                    title="Total Signups"
                    value={analytics?.totalSignups || 0}
                    icon={TrendingUp}
                    trend={analytics?.userGrowthTrend}
                    iconClass="success"
                />

                <AdminStatsCard
                    title="New Users (Period)"
                    value={analytics?.newUsers || 0}
                    icon={Users}
                    trend={analytics?.newUsersTrend}
                    iconClass="primary"
                />

                <AdminStatsCard
                    title="Active Rate"
                    value={`${analytics?.activeRate || 0}%`}
                    icon={UserCheck}
                    trend={analytics?.activeRateTrend}
                    iconClass="success"
                />

                <AdminStatsCard
                    title="Conversion Rate"
                    value={`${analytics?.conversionRate || 0}%`}
                    icon={CreditCard}
                    trend={analytics?.conversionTrend}
                    iconClass="warning"
                />
            </div>

            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
                gap: '1.5rem',
                marginTop: '2rem'
            }}>
                <div className="admin-card glass-premium">
                    <div className="admin-card-header">
                        <h2 className="admin-card-title">User Growth Trend</h2>
                    </div>
                    <div style={{ marginTop: '1.5rem' }}>
                        <AdminChart.Line data={userGrowthData} height={200} />
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1rem' }}>
                            {userGrowthData.map(d => (
                                <span key={d.label} style={{ fontSize: '0.75rem', color: 'var(--admin-text-muted)' }}>{d.label}</span>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="admin-card glass-premium">
                    <div className="admin-card-header">
                        <h2 className="admin-card-title">Subscription Distribution (%)</h2>
                    </div>
                    <div style={{ marginTop: '1.5rem' }}>
                        <AdminChart.Bar data={subDistributionData} height={200} color="var(--admin-accent-warning)" />
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1rem', padding: '0 10%' }}>
                            {subDistributionData.map(d => (
                                <span key={d.label} style={{ fontSize: '0.75rem', color: 'var(--admin-text-muted)' }}>{d.label}</span>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            <div className="admin-card" style={{ marginTop: '1.5rem' }}>
                <div className="admin-card-header">
                    <h2 className="admin-card-title">Conversion Funnel</h2>
                </div>
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                    gap: '1rem',
                    marginTop: '1rem'
                }}>
                    <div style={{
                        padding: '1.5rem',
                        background: 'var(--admin-bg-tertiary)',
                        borderRadius: '12px',
                        textAlign: 'center',
                        border: '1px solid var(--admin-border-color)'
                    }}>
                        <div style={{
                            fontSize: '2.25rem',
                            fontWeight: 800,
                            color: 'var(--admin-text-primary)'
                        }}>
                            {analytics?.totalSignups || 0}
                        </div>
                        <div style={{ color: 'var(--admin-text-muted)', marginTop: '0.5rem', fontWeight: 600 }}>
                            Total Signups
                        </div>
                    </div>

                    <div style={{
                        padding: '1.5rem',
                        background: 'var(--admin-bg-tertiary)',
                        borderRadius: '12px',
                        textAlign: 'center',
                        border: '1px solid var(--admin-border-color)'
                    }}>
                        <div style={{
                            fontSize: '2.25rem',
                            fontWeight: 800,
                            color: 'var(--admin-text-primary)'
                        }}>
                            {analytics?.activeUsers || 0}
                        </div>
                        <div style={{ color: 'var(--admin-text-muted)', marginTop: '0.5rem', fontWeight: 600 }}>
                            Active Users
                        </div>
                    </div>

                    <div style={{
                        padding: '1.5rem',
                        background: 'var(--admin-bg-tertiary)',
                        borderRadius: '12px',
                        textAlign: 'center',
                        border: '1px solid var(--admin-border-color)'
                    }}>
                        <div style={{
                            fontSize: '2.25rem',
                            fontWeight: 800,
                            color: 'var(--admin-text-primary)'
                        }}>
                            {analytics?.totalPrompts || 0}
                        </div>
                        <div style={{ color: 'var(--admin-text-muted)', marginTop: '0.5rem', fontWeight: 600 }}>
                            Total AI Prompts
                        </div>
                    </div>

                    <div style={{
                        padding: '1.5rem',
                        background: 'var(--admin-bg-tertiary)',
                        borderRadius: '12px',
                        textAlign: 'center',
                        border: '1px solid var(--admin-accent-warning)'
                    }}>
                        <div style={{
                            fontSize: '2.25rem',
                            fontWeight: 800,
                            color: 'var(--admin-accent-warning)'
                        }}>
                            {analytics?.conversionRate || 0}%
                        </div>
                        <div style={{ color: 'var(--admin-text-muted)', marginTop: '0.5rem', fontWeight: 600 }}>
                            Conversion Rate
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Analytics;
