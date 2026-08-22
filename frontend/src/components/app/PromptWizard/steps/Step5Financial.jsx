import React from 'react';

const Step5Financial = ({ data, updateData }) => {
    const budgets = [
        { id: 'low', label: 'Government Sponsored (Low Cost)', desc: 'Primarily looking for KUCCPS placement with minimal fee top-up.' },
        { id: 'mid', label: 'Moderate Budget', desc: 'Can afford standard public or private university fees.' },
        { id: 'high', label: 'High / Self-Sponsored', desc: 'Budget is not a primary concern for the right course.' }
    ];

    return (
        <div className="step-content">
            <h2 className="step-label">Financial Planning</h2>
            <p className="step-description">Tell us about your fee budget to filter institutions.</p>

            <div style={{ marginTop: '2rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {budgets.map(budget => (
                    <div
                        key={budget.id}
                        onClick={() => updateData({ budgetRange: budget.id })}
                        style={{
                            padding: '1.25rem',
                            borderRadius: '12px',
                            border: '2px solid',
                            borderColor: data.budgetRange === budget.id ? 'var(--color-secondary)' : '#f1f5f9',
                            cursor: 'pointer',
                            transition: 'all 0.2s'
                        }}
                    >
                        <div style={{ fontWeight: '700', marginBottom: '0.25rem' }}>{budget.label}</div>
                        <div style={{ fontSize: '0.85rem', color: '#64748b' }}>{budget.desc}</div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Step5Financial;
