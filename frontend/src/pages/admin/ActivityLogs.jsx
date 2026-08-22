import { useState, useEffect } from 'react';
import { Activity, Clock, User, CreditCard } from 'lucide-react';
import adminApi from '../../api/adminApi';
import '../../styles/AdminTheme.css';

const ActivityLogs = () => {
    const [activities, setActivities] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadActivityLogs();
    }, []);

    const loadActivityLogs = async () => {
        try {
            setLoading(true);
            const data = await adminApi.getActivityLogs(50);
            // Backend returns chat/prompt logs, normalize to a consistent activity shape
            const normalized = (data || []).map((entry) => ({
                type: 'ai_prompt',
                user_email: entry.user?.email || entry.user?.username || 'Unknown User',
                description: entry.payload_summary || entry.result_summary || 'AI Prompt Submission',
                timestamp: entry.created_at,
            }));
            setActivities(normalized);
        } catch (err) {
            console.error('Failed to load activity logs:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const getActivityIcon = (type) => {
        switch (type) {
            case 'login':
            case 'signup':
                return <User size={16} />;
            case 'subscription_change':
                return <CreditCard size={16} />;
            default:
                return <Activity size={16} />;
        }
    };

    const getActivityColor = (type) => {
        switch (type) {
            case 'login':
                return 'success';
            case 'signup':
                return 'primary';
            case 'subscription_change':
                return 'warning';
            default:
                return 'primary';
        }
    };

    if (loading) {
        return (
            <div>
                <h1 style={{ marginBottom: '2rem', color: 'var(--admin-text-primary)' }}>
                    Activity Logs
                </h1>
                <p style={{ color: 'var(--admin-text-muted)' }}>Loading activity logs...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div>
                <h1 style={{ marginBottom: '2rem', color: 'var(--admin-text-primary)' }}>
                    Activity Logs
                </h1>
                <div className="admin-card">
                    <p style={{ color: 'var(--admin-accent-danger)' }}>
                        Failed to load activity logs: {error}
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
            <h1 style={{ marginBottom: '2rem', color: 'var(--admin-text-primary)' }}>
                Activity Logs
            </h1>

            <div className="admin-card">
                <div className="admin-card-header">
                    <h2 className="admin-card-title">Recent Activity</h2>
                    <button className="admin-btn admin-btn-secondary" onClick={loadActivityLogs}>
                        <Activity size={16} />
                        Refresh
                    </button>
                </div>

                {activities.length === 0 ? (
                    <div style={{ padding: '2rem', textAlign: 'center' }}>
                        <p style={{ color: 'var(--admin-text-muted)' }}>
                            No activity logs available
                        </p>
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '1rem' }}>
                        {activities.map((activity, index) => (
                            <div
                                key={index}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '1rem',
                                    padding: '1rem',
                                    background: 'var(--admin-bg-tertiary)',
                                    borderRadius: '8px',
                                    border: '1px solid var(--admin-border-color)'
                                }}
                            >
                                <div className={`admin-stat-icon ${getActivityColor(activity.type)}`}>
                                    {getActivityIcon(activity.type)}
                                </div>
                                <div style={{ flex: 1 }}>
                                    <div style={{
                                        fontWeight: 500,
                                        color: 'var(--admin-text-primary)',
                                        marginBottom: '0.25rem'
                                    }}>
                                        {activity.user_email || activity.user_name || 'Unknown User'}
                                    </div>
                                    <div style={{ fontSize: '0.875rem', color: 'var(--admin-text-muted)' }}>
                                        {activity.description || activity.type}
                                    </div>
                                </div>
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem',
                                    color: 'var(--admin-text-muted)',
                                    fontSize: '0.875rem'
                                }}>
                                    <Clock size={14} />
                                    {activity.timestamp
                                        ? new Date(activity.timestamp).toLocaleString()
                                        : 'Just now'}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ActivityLogs;
