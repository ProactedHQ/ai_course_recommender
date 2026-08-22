import React from 'react';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';
import { useToastInternal } from '../../context/ToastContext';

const ToastContainer = () => {
    const { toasts, removeToast } = useToastInternal();

    if (toasts.length === 0) return null;

    return (
        <div style={{
            position: 'fixed',
            top: '1.5rem',
            right: '1.5rem',
            zIndex: 9999,
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
            pointerEvents: 'none'
        }}>
            {toasts.map(toast => (
                <ToastItem key={toast.id} toast={toast} onRemove={() => removeToast(toast.id)} />
            ))}
        </div>
    );
};

const ToastItem = ({ toast, onRemove }) => {
    const getIcon = () => {
        switch (toast.type) {
            case 'success': return <CheckCircle size={18} color="var(--admin-accent-success)" />;
            case 'error': return <AlertCircle size={18} color="var(--admin-accent-danger)" />;
            case 'warning': return <AlertTriangle size={18} color="var(--admin-accent-warning)" />;
            case 'info': return <Info size={18} color="var(--admin-accent-primary)" />;
            default: return null;
        }
    };

    return (
        <div
            className="admin-dashboard-fade-in"
            style={{
                minWidth: '300px',
                maxWidth: '450px',
                background: 'rgba(20, 27, 45, 0.85)',
                backdropFilter: 'blur(12px)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '12px',
                padding: '1rem',
                boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.4)',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.875rem',
                pointerEvents: 'auto',
                animation: 'toastSlideIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)'
            }}
        >
            <div style={{ marginTop: '2px' }}>{getIcon()}</div>
            <div style={{ flex: 1 }}>
                <div style={{
                    color: 'var(--admin-text-primary)',
                    fontSize: '0.925rem',
                    fontWeight: 500,
                    lineHeight: '1.4'
                }}>
                    {toast.message}
                </div>
            </div>
            <button
                onClick={onRemove}
                style={{
                    background: 'none',
                    border: 'none',
                    padding: '4px',
                    color: 'var(--admin-text-muted)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    borderRadius: '4px',
                }}
                className="admin-btn-secondary"
            >
                <X size={14} />
            </button>

            <style>{`
                @keyframes toastSlideIn {
                    from { transform: translateX(120%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `}</style>
        </div>
    );
};

export default ToastContainer;
