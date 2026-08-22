import React from 'react';

const Step3CareerGoals = ({ data, updateData }) => {
    return (
        <div className="step-content">
            <h2 className="step-label">Career Goals</h2>
            <p className="step-description">What do you aspire to be? Describe your dream career.</p>

            <div style={{ marginTop: '2rem' }}>
                <textarea
                    placeholder="e.g. I want to become a Software Engineer at a global tech firm or start my own AI startup..."
                    style={{
                        width: '100%',
                        minHeight: '200px',
                        padding: '1rem',
                        borderRadius: '12px',
                        border: '1px solid #e2e8f0',
                        fontSize: '1rem',
                        fontFamily: 'inherit'
                    }}
                    value={data.careerAspirations || ''}
                    onChange={(e) => updateData({ careerAspirations: e.target.value })}
                />
            </div>
        </div>
    );
};

export default Step3CareerGoals;
