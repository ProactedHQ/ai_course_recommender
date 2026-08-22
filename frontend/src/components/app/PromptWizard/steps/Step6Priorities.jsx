import React from 'react';
import FieldHelp from '../FieldHelp.jsx';

const Step6Priorities = ({ data, updateData, isConfirmed, onConfirmToggle, errors }) => {

    const handleWeightChange = (key, weight) => {
        const newItems = data.items.map(item => {
            if (item.key === key) {
                const val = parseFloat(weight) || 0;
                return { ...item, weight: val };
            }
            return item;
        });

        const total = newItems.reduce((sum, item) => sum + item.weight, 0);
        updateData({ items: newItems, total_weight: total });
    };

    const weightError = errors?.['student_profile.decision_priorities.total_weight'];
    const confirmError = errors?.['confirmation'];

    return (
        <div className="wizard-step step-priorities-flat">
            <h2 className="step-title">
                Priority Allocation <span className="required-asterisk">*</span>
                <FieldHelp 
                    title="Priority Allocation" 
                    content={<><strong>💡 What to do:</strong> Divide 100% amongst the 5 factors below based on what matters MOST to you. If Salary is everything, give it 80% and divide the remaining 20% elsewhere.<br/><br/><strong>Why it matters:</strong> This is the <strong>biggest</strong> factor controlling the AI. If you put high weight on "Social impact", the AI will ignore high-paying corporate jobs and recommend nursing, teaching, or NGOs instead.</>} 
                />
            </h2>
            <p className="step-description">Distribute exactly 100% across your priorities.</p>

            <div className="priorities-flat-grid">
                <div className="total-indicator-premium">
                    <div className={`percentage-circle ${Math.abs(data.total_weight - 100) < 0.00001 ? 'valid' : 'invalid'}`}>
                        <span className="current-total">{Number(data.total_weight.toFixed(5))}</span>
                        <span className="total-target">/ 100%</span>
                    </div>
                    {weightError && <span className="field-error-text text-center">{weightError}</span>}
                </div>

                <div className="priorities-inputs-premium">
                    {data.items.map(item => (
                        <div key={item.key} className="priority-input-row-refined">
                            <div className="p-info-mini">
                                <span className="p-title-mini">{item.label}</span>
                            </div>
                            <div className="p-input-wrapper-mini">
                                <input
                                    type="number"
                                    min="0"
                                    max="100"
                                    step="any"
                                    value={item.weight}
                                    onChange={(e) => handleWeightChange(item.key, e.target.value)}
                                    className="p-number-input-premium"
                                />
                                <span className="p-percent-suffix">%</span>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="compact-confirmation-premium">
                    <label className={`premium-checkbox-compact ${confirmError ? 'input-error-border' : ''}`}>
                        <input
                            type="checkbox"
                            checked={isConfirmed}
                            onChange={(e) => onConfirmToggle(e.target.checked)}
                        />
                        <span className="premium-check-box"></span>
                        <div className="premium-confirm-labels">
                            <span className="confirm-main-mini">Confirm and Proceed</span>
                            <span className="confirm-sub-mini">I verify that the allocated priorities reflect my preferences.</span>
                        </div>
                    </label>
                    {confirmError && <span className="field-error-text mt-1">{confirmError}</span>}
                </div>
            </div>
        </div>
    );
};

export default Step6Priorities;
