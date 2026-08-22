import React from 'react';

const Step6Review = ({ data, onConfirmToggle, isConfirmed, validationStates }) => {
    const profile = data || {};

    // Explicit list of what is missing
    const missingItems = [];
    if (!validationStates[0]) missingItems.push("Academic: Add at least 3 subjects with grades.");
    if (!validationStates[1]) missingItems.push("Personal: Provide a self-description (min. 10 chars) and select at least one strength.");
    if (!validationStates[2]) missingItems.push("Practical: Select a preferred study location.");
    if (!validationStates[3]) missingItems.push("Interests: Select at least one interest/hobby.");

    return (
        <div className="wizard-step">
            <h2 className="step-title">Review & Confirm</h2>
            <p className="step-description">Please double-check your summary before generating recommendations.</p>

            {missingItems.length > 0 && (
                <div className="wizard-validation-alert">
                    <div className="alert-header-premium">
                        <span className="alert-icon">⚠️</span>
                        <h4>Action Required</h4>
                    </div>
                    <ul className="alert-body-list">
                        {missingItems.map((item, idx) => <li key={idx}>{item}</li>)}
                    </ul>
                    <p className="alert-footer-note">Use the navigation bar above to jump back and complete these sections.</p>
                </div>
            )}

            <div className="review-container">
                <div className="review-section">
                    <h4 className="review-section-title">Academic Profile</h4>
                    <div className="review-summary-grid">
                        <div className="summary-item">
                            <span className="summary-label">Main Subjects:</span>
                            <span className="summary-value">{(profile.kcse?.subjects || []).filter(s => s.name && s.grade).length} entered</span>
                        </div>
                        <div className="summary-item">
                            <span className="summary-label">Custom Subjects:</span>
                            <span className="summary-value">{profile.kcse?.custom_subjects?.length || 0} entered</span>
                        </div>
                    </div>
                </div>

                <div className="review-section">
                    <h4 className="review-section-title">Practical Factors</h4>
                    <div className="review-summary-grid">
                        <div className="summary-item">
                            <span className="summary-label">Preferred Location:</span>
                            <span className="summary-value">{profile.practical_factors?.preferred_location || 'Not set'}</span>
                        </div>
                        <div className="summary-item">
                            <span className="summary-label">Study Time:</span>
                            <span className="summary-value">{profile.practical_factors?.time_hours_per_week || 0} hrs/week</span>
                        </div>
                    </div>
                </div>

                <div className="review-section">
                    <h4 className="review-section-title">Interests & Goals</h4>
                    <div className="review-summary-grid">
                        <div className="summary-item">
                            <span className="summary-label">Key Hobbies:</span>
                            <span className="summary-value">{(profile.interests_exposure?.interests_hobbies || []).join(', ') || 'None selected'}</span>
                        </div>
                    </div>
                </div>

                <div className="confirmation-box">
                    <label className="checkbox-container">
                        <input
                            type="checkbox"
                            checked={isConfirmed}
                            onChange={(e) => onConfirmToggle(e.target.checked)}
                            disabled={missingItems.length > 0}
                        />
                        <span className="checkmark"></span>
                        <span className={`confirmation-text ${missingItems.length > 0 ? 'opacity-50' : ''}`}>
                            {missingItems.length > 0
                                ? "Complete the missing sections above to enable confirmation."
                                : "I confirm that the information provided is accurate and I am ready to see my course matches."
                            }
                        </span>
                    </label>
                </div>
            </div>
        </div>
    );
};

export default Step6Review;
