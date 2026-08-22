import { useEffect, useState } from 'react';
import { MessageSquare, Calendar, Cpu, ChevronDown, Search, SlidersHorizontal, AlertCircle } from 'lucide-react';
import adminApi from '../../api/adminApi';
import { useAdminData } from '../../hooks/useAdminData';
import '../../styles/AdminTheme.css';

const ChatLogs = () => {
    const { fetchData, loading: dataLoading } = useAdminData();
    const [logs, setLogs] = useState([]);
    const [expandedLog, setExpandedLog] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        loadLogs();
    }, []);

    const loadLogs = async () => {
        try {
            const data = await fetchData('chat_logs', () => adminApi.getActivityLogs());
            setLogs(data);
        } catch (err) {
            console.error('Failed to load logs:', err);
        }
    };

    const toggleExpand = (id) => {
        setExpandedLog(expandedLog === id ? null : id);
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const filteredLogs = logs.filter(log =>
        log.user_email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.description?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (dataLoading && !logs.length) return (
        <div className="admin-dashboard-fade-in" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '300px', color: 'var(--admin-text-muted)' }}>
            <div className="admin-loading-spinner" style={{ marginRight: '1rem' }}></div>
            Retrieving AI audit transcripts...
        </div>
    );

    return (
        <div className="admin-dashboard-fade-in">
            <div style={{ marginBottom: '2.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '1.5rem' }}>
                <div>
                    <h1 style={{ color: 'var(--admin-text-primary)', fontSize: '2rem', fontWeight: 800, marginBottom: '0.5rem' }}>AI Interaction Audit</h1>
                    <p style={{ color: 'var(--admin-text-muted)', margin: 0 }}>Review and audit AI-driven course recommendations and student queries.</p>
                </div>
                <div style={{ position: 'relative', width: '350px', maxWidth: '100%' }}>
                    <Search size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--admin-text-muted)' }} />
                    <input
                        type="text"
                        placeholder="Search by user or query contents..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="admin-search-input"
                        style={{
                            width: '100%',
                            padding: '12px 12px 12px 42px',
                            background: 'var(--admin-bg-secondary)',
                            border: '1px solid var(--admin-border-color)',
                            borderRadius: '12px',
                            color: 'var(--admin-text-primary)',
                            fontSize: '0.95rem',
                            outline: 'none'
                        }}
                    />
                </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {filteredLogs.length === 0 ? (
                    <div className="admin-card glass-premium" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
                        <MessageSquare size={48} style={{ color: 'var(--admin-text-muted)', marginBottom: '1.5rem', opacity: 0.3 }} />
                        <h3 style={{ color: 'var(--admin-text-primary)', marginBottom: '0.5rem' }}>No Logs Found</h3>
                        <p style={{ color: 'var(--admin-text-muted)' }}>No AI interaction logs match your current search criteria.</p>
                    </div>
                ) : (
                    filteredLogs.map((log) => (
                        <div key={log.id} className={`admin-card glass-premium ${expandedLog === log.id ? 'expanded' : ''}`} style={{ padding: 0, overflow: 'hidden' }}>
                            <div
                                onClick={() => toggleExpand(log.id)}
                                style={{
                                    padding: '1.5rem',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'space-between',
                                    background: expandedLog === log.id ? 'rgba(255,255,255,0.02)' : 'transparent',
                                    transition: 'background 0.2s ease'
                                }}
                            >
                                <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', flex: 1 }}>
                                    <div style={{
                                        width: '44px',
                                        height: '44px',
                                        borderRadius: '12px',
                                        background: 'rgba(59, 130, 246, 0.1)',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        color: 'var(--admin-accent-primary)',
                                        flexShrink: 0
                                    }}>
                                        <Cpu size={22} />
                                    </div>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.35rem' }}>
                                            <span style={{ fontWeight: 700, color: 'var(--admin-text-primary)', fontSize: '1.05rem' }}>{log.user_email || 'System User'}</span>
                                            <span className="admin-badge primary" style={{ fontSize: '0.75rem', fontWeight: 600 }}>KeDira AI</span>
                                        </div>
                                        <div style={{ color: 'var(--admin-text-muted)', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
                                            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><Calendar size={14} /> {formatDate(log.created_at)}</span>
                                            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><AlertCircle size={14} /> Success</span>
                                        </div>
                                    </div>
                                </div>
                                <div style={{ color: 'var(--admin-text-muted)', transition: 'transform 0.3s ease', transform: expandedLog === log.id ? 'rotate(180deg)' : 'rotate(0deg)' }}>
                                    <ChevronDown size={20} />
                                </div>
                            </div>

                            {expandedLog === log.id && (
                                <div className="fade-in" style={{ padding: '0 1.5rem 1.75rem', borderTop: '1px solid var(--admin-border-color)', background: 'rgba(255,255,255,0.01)' }}>
                                    <div style={{ marginTop: '1.5rem' }}>
                                        <div style={{ color: 'var(--admin-accent-primary)', fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase', marginBottom: '0.85rem', letterSpacing: '0.08em', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                            <div style={{ width: '4px', height: '12px', background: 'currentColor', borderRadius: '2px' }} />
                                            User Prompt Input
                                        </div>
                                        <div style={{
                                            padding: '1.5rem',
                                            background: 'var(--admin-bg-tertiary)',
                                            borderRadius: '12px',
                                            color: 'var(--admin-text-secondary)',
                                            lineHeight: 1.7,
                                            fontSize: '0.95rem',
                                            border: '1px solid var(--admin-border-color)'
                                        }}>
                                            {log.description}
                                        </div>
                                    </div>

                                    {log.details?.response && (
                                        <div style={{ marginTop: '1.75rem' }}>
                                            <div style={{ color: 'var(--admin-accent-success)', fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase', marginBottom: '0.85rem', letterSpacing: '0.08em', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                <div style={{ width: '4px', height: '12px', background: 'currentColor', borderRadius: '2px' }} />
                                                AI System Response
                                            </div>
                                            <div style={{
                                                padding: '1.5rem',
                                                background: 'rgba(16, 185, 129, 0.05)',
                                                borderRadius: '12px',
                                                color: 'var(--admin-text-secondary)',
                                                lineHeight: 1.7,
                                                fontSize: '0.95rem',
                                                border: '1px solid rgba(16, 185, 129, 0.15)'
                                            }}>
                                                {log.details.response}
                                            </div>
                                        </div>
                                    )}

                                    <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
                                        <button className="admin-btn admin-btn-secondary" style={{ fontSize: '0.85rem' }}>
                                            Download Transcript
                                        </button>
                                        <button className="admin-btn admin-btn-secondary" style={{ fontSize: '0.85rem', border: '1px solid var(--admin-accent-danger)', color: 'var(--admin-accent-danger)' }}>
                                            Flag Interaction
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default ChatLogs;
