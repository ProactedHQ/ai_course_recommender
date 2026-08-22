import React from 'react';

const Step4LocationPref = ({ data, updateData }) => {
    const regions = [
        'Nairobi Area',
        'Central Kenya',
        'Coastal Region',
        'Rift Valley',
        'Western Kenya',
        'Nyanza Region',
        'Eastern Kenya',
        'No Preference'
    ];

    return (
        <div className="step-content">
            <h2 className="step-label">Location Preferences</h2>
            <p className="step-description">Where would you prefer to study?</p>

            <div style={{ marginTop: '2rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {regions.map(region => (
                    <label
                        key={region}
                        style={{
                            padding: '1rem',
                            borderRadius: '8px',
                            border: '1px solid #e2e8f0',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '1rem',
                            cursor: 'pointer',
                            backgroundColor: data.regionPref === region ? '#f8fafc' : 'transparent'
                        }}
                    >
                        <input
                            type="radio"
                            name="region"
                            checked={data.regionPref === region}
                            onChange={() => updateData({ regionPref: region })}
                        />
                        <span>{region}</span>
                    </label>
                ))}
            </div>
        </div>
    );
};

export default Step4LocationPref;
