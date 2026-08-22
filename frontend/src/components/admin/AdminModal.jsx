import React from 'react';
import { X } from 'lucide-react';

const AdminModal = ({ isOpen, onClose, title, children, footer }) => {
    if (!isOpen) return null;

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            background: 'rgba(0, 0, 0, 0.6)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 10000,
            padding: '1rem',
            animation: 'modalFadeIn 0.2s ease'
        }}>
            <div
                className="admin-card"
                style={{
                    width: '100%',
                    maxWidth: '500px',
                    padding: 0,
                    overflow: 'hidden',
                    animation: 'modalSlideUp 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)'
                }}
            >
                <div style={{
                    padding: '1.25rem 1.5rem',
                    borderBottom: '1px solid var(--admin-border-color)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    background: 'var(--admin-bg-tertiary)'
                }}>
                    <h3 style={{
                        margin: 0,
                        fontFamily: 'var(--admin-font-heading)',
                        fontSize: '1.25rem',
                        color: 'var(--admin-text-primary)'
                    }}>
                        {title}
                    </h3>
                    <button
                        onClick={onClose}
                        style={{
                            background: 'none',
                            border: 'none',
                            color: 'var(--admin-text-muted)',
                            cursor: 'pointer',
                            padding: '4px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                        }}
                    >
                        <X size={20} />
                    </button>
                </div>

                <div style={{ padding: '1.5rem' }}>
                    {children}
                </div>

                {footer && (
                    <div style={{
                        padding: '1.25rem 1.5rem',
                        borderTop: '1px solid var(--admin-border-color)',
                        display: 'flex',
                        justifyContent: 'flex-end',
                        gap: '0.75rem',
                        background: 'var(--admin-bg-tertiary)'
                    }}>
                        {footer}
                    </div>
                )}
            </div>

            <style>{`
                @keyframes modalFadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                @keyframes modalSlideUp {
                    from { transform: translateY(20px); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }
            `}</style>
        </div>
    );
};

export default AdminModal;
