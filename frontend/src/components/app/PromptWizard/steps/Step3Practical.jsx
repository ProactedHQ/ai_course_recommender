import React from 'react';
import { countWords } from '../../../../utils/wizardValidation.js';
import FieldHelp from '../FieldHelp.jsx';

const Step3Practical = ({ data, updateData, errors }) => {
    const locationsPool = [
        "Central Province",
        "Coast Province",
        "Eastern Province",
        "Nairobi Province",
        "North Eastern Province",
        "Nyanza Province",
        "Rift Valley Province",
        "Western Province"
    ];

    const constraintsWordCount = countWords(data.constraints_notes);

    return (
        <div className="wizard-step">
            <h2 className="step-title">Practical Factors</h2>
            <p className="step-description">Help us understand your time and budget constraints.</p>

            <div className="form-section">
                <label className="form-label">
                    Available Study Time (Hours/Week) <span className="required-asterisk">*</span>
                    <FieldHelp 
                        title="Available Study Time" 
                        content={<><strong>💡 What to enter:</strong> How many hours per week can you realistically dedicate to attending classes and studying?<br/><br/><strong>Why it matters:</strong> Prevents the AI from recommending highly intensive 60-hour/week degrees if you only have part-time availability.</>} 
                    />
                </label>
                <input
                    type="number"
                    className={`form-input ${errors?.['student_profile.practical_factors.time_hours_per_week'] ? 'input-error' : ''}`}
                    placeholder="e.g. 40"
                    min="1"
                    max="168"
                    value={data.time_hours_per_week || ''}
                    onChange={(e) => updateData({ time_hours_per_week: parseInt(e.target.value) || 0 })}
                />
                {errors?.['student_profile.practical_factors.time_hours_per_week'] && (
                    <span className="field-error-text">{errors['student_profile.practical_factors.time_hours_per_week']}</span>
                )}
            </div>

            <div className="form-section">
                <label className="form-label">
                    Budget Range (KES / Year) <span className="required-asterisk">*</span>
                    <FieldHelp 
                        title="Budget Range" 
                        content={<><strong>💡 What to enter:</strong> What's the maximum amount you or your sponsors can afford to pay for tuition per year?<br/><br/><strong>Why it matters:</strong> Ensures we don't confidently recommend expensive private universities if you're looking for government-sponsored public options or TVETs.</>} 
                    />
                </label>
                <input
                    type="number"
                    className={`form-input ${errors?.['student_profile.practical_factors.budget_kes_estimate'] ? 'input-error' : ''}`}
                    placeholder="e.g. 150000"
                    value={data.budget_kes_estimate || ''}
                    onChange={(e) => updateData({ budget_kes_estimate: parseInt(e.target.value) || 0 })}
                />
                {errors?.['student_profile.practical_factors.budget_kes_estimate'] && (
                    <span className="field-error-text">{errors['student_profile.practical_factors.budget_kes_estimate']}</span>
                )}
            </div>

            <div className="form-section">
                <label className="form-label">
                    Preferred Location <span className="required-asterisk">*</span>
                    <FieldHelp 
                        title="Preferred Location" 
                        content={
                            <>
                                <strong>💡 What to select:</strong> Which province would you prefer to study in?<br/><br/>
                                <strong>Counties per Province:</strong>
                                <ul style={{ paddingLeft: '1.2rem', marginTop: '0.4rem', fontSize: '0.9em' }}>
                                    <li><strong>Central:</strong> Nyeri, Kirinyaga, Murang'a, Kiambu</li>
                                    <li><strong>Coast:</strong> Mombasa, Kwale, Kilifi, Tana River, Lamu, Taita Taveta</li>
                                    <li><strong>Eastern:</strong> Embu, Kitui, Machakos, Makueni, Meru, Tharaka-Nithi, Isiolo</li>
                                    <li><strong>Nairobi:</strong> Nairobi City</li>
                                    <li><strong>North Eastern:</strong> Garissa, Wajir, Mandera</li>
                                    <li><strong>Nyanza:</strong> Kisumu, Homa Bay, Migori, Kisii, Nyamira, Siaya</li>
                                    <li><strong>Rift Valley:</strong> Nakuru, Uasin Gishu, Elgeyo-Marakwet, Nandi, Baringo, Laikipia, Samburu, West Pokot, Turkana, Trans Nzoia, Bomet, Kericho, Narok, Kajiado, Nyandarua</li>
                                    <li><strong>Western:</strong> Kakamega, Vihiga, Bungoma, Busia</li>
                                </ul>
                            </>
                        } 
                    />
                </label>
                <select
                    className={`form-select ${errors?.['student_profile.practical_factors.preferred_location'] ? 'input-error' : ''}`}
                    value={data.preferred_location}
                    onChange={(e) => updateData({ preferred_location: e.target.value })}
                >
                    <option value="">Select preference</option>
                    {locationsPool.map(loc => (
                        <option key={loc} value={loc}>{loc}</option>
                    ))}
                </select>
                {errors?.['student_profile.practical_factors.preferred_location'] && (
                    <span className="field-error-text">{errors['student_profile.practical_factors.preferred_location']}</span>
                )}
            </div>

            <div className="form-section">
                <div className="label-with-counter">
                    <label className="form-label">
                        Constraint Notes (Optional)
                        <FieldHelp 
                            title="Constraint Notes" 
                            content={<><strong>💡 What to write (optional):</strong> Are there any other hard limits we should know? Like a disability requiring specific facilities, or a need for evening classes only?</>} 
                        />
                    </label>
                    <span className={`word-counter ${constraintsWordCount > 30 ? 'warning' : 'success'}`}>
                        {constraintsWordCount} / 30 words
                    </span>
                </div>
                <textarea
                    className={`form-textarea ${errors?.['student_profile.practical_factors.constraints_notes'] ? 'input-error' : ''}`}
                    placeholder="Any other practical factors we should consider? (max 30 words)"
                    value={data.constraints_notes}
                    onChange={(e) => updateData({ constraints_notes: e.target.value })}
                />
                {errors?.['student_profile.practical_factors.constraints_notes'] && (
                    <span className="field-error-text">{errors['student_profile.practical_factors.constraints_notes']}</span>
                )}
            </div>
        </div>
    );
};

export default Step3Practical;
