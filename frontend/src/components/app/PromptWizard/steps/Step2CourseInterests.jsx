import React from 'react';

const Step2CourseInterests = ({ data, updateData }) => {
    const domains = [
        { id: 'eng', label: 'Engineering & Technology', icon: '⚙️' },
        { id: 'med', label: 'Medicine & Health Sciences', icon: '🩺' },
        { id: 'biz', label: 'Business & Economics', icon: '💼' },
        { id: 'ict', label: 'ICT & Computing', icon: '💻' },
        { id: 'law', label: 'Law & Governance', icon: '⚖️' },
        { id: 'art', label: 'Arts & Humanities', icon: '🎨' },
        { id: 'sci', label: 'Pure & Applied Sciences', icon: '🧪' },
        { id: 'edu', label: 'Education', icon: '📚' }
    ];

    const toggleDomain = (id) => {
        const current = data.interestDomains || [];
        const updated = current.includes(id)
            ? current.filter(item => item !== id)
            : [...current, id];
        updateData({ interestDomains: updated });
    };

    return (
        <div className="step-content">
            <h2 className="step-label">Course Interests</h2>
            <p className="step-description">Select the fields you are most interested in studying.</p>

            <div className="interests-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem', marginTop: '2rem' }}>
                {domains.map(domain => (
                    <div
                        key={domain.id}
                        className={`interest-card ${data.interestDomains?.includes(domain.id) ? 'selected' : ''}`}
                        onClick={() => toggleDomain(domain.id)}
                        style={{
                            padding: '1.5rem',
                            borderRadius: '12px',
                            border: '2px solid',
                            borderColor: data.interestDomains?.includes(domain.id) ? 'var(--color-secondary)' : '#f1f5f9',
                            backgroundColor: data.interestDomains?.includes(domain.id) ? '#f0fdfa' : '#ffffff',
                            cursor: 'pointer',
                            textAlign: 'center',
                            transition: 'all 0.2s'
                        }}
                    >
                        <span style={{ fontSize: '2rem', display: 'block', marginBottom: '0.75rem' }}>{domain.icon}</span>
                        <span style={{ fontWeight: '600', fontSize: '0.9rem' }}>{domain.label}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Step2CourseInterests;
