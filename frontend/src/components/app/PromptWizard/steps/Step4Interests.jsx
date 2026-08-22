import React from 'react';
import { countWords, countSentences } from '../../../../utils/wizardValidation.js';
import FieldHelp from '../FieldHelp.jsx';

const Step4Interests = ({ data, updateData, errors }) => {
    const interestsPool = ["Technology", "Science", "Arts & Design", "Business", "Health", "Social Service", "Languages", "Sports", "Nature & Environment", "Music", "Mathematics", "Writing"];
    const extracurricularsPool = ["Sports Teams", "Science Club", "Drama/Music", "Debate Club", "Scouting/First Aid", "Volunteering", "Computer Club", "Art Club", "Student Leadership"];

    const toggleItem = (field, item) => {
        const newList = data[field].includes(item)
            ? data[field].filter(i => i !== item)
            : [...data[field], item];
        updateData({ [field]: newList });
    };

    const words = countWords(data.exposure_notes);
    const sentences = countSentences(data.exposure_notes);

    return (
        <div className="wizard-step">
            <h2 className="step-title">Interests & Extracurriculars</h2>
            <p className="step-description">Tell us what you enjoy doing outside the classroom.</p>

            <div className="form-section">
                <label className="form-label">
                    Core Interests <span className="required-asterisk">*</span>
                    <FieldHelp 
                        title="Core Interests" 
                        content={<><strong>💡 What to select:</strong> What broad topics organically capture your attention? (e.g., do you spend hours reading about tech, or analyzing business trends?)<br/><br/><strong>Why it matters:</strong> Passion is the fuel for a long-term career. We map these interests to courses you'll genuinely enjoy studying.</>} 
                    />
                </label>
                <div className="chip-group">
                    {interestsPool.map(item => (
                        <button
                            key={item}
                            className={`chip ${data.interests_hobbies.includes(item) ? 'active' : ''}`}
                            onClick={() => toggleItem('interests_hobbies', item)}
                        >
                            {item}
                        </button>
                    ))}
                </div>
                {errors?.['student_profile.interests_exposure.interests_hobbies'] && (
                    <span className="field-error-text">{errors['student_profile.interests_exposure.interests_hobbies']}</span>
                )}
            </div>

            <div className="form-section">
                <label className="form-label">
                    Extracurricular Activities
                    <FieldHelp 
                        title="Extracurricular Activities" 
                        content={<><strong>💡 What to select:</strong> Clubs, sports, or groups you were actively involved in during high school.<br/><br/><strong>Why it matters:</strong> This highlights practical team skills and leadership that many top university programs look for.</>} 
                    />
                </label>
                <div className="chip-group">
                    {extracurricularsPool.map(item => (
                        <button
                            key={item}
                            className={`chip ${data.extracurriculars.includes(item) ? 'active' : ''}`}
                            onClick={() => toggleItem('extracurriculars', item)}
                        >
                            {item}
                        </button>
                    ))}
                </div>
            </div>

            <div className="form-section">
                <div className="label-with-counter">
                    <label className="form-label">
                        Exposure Notes (Optional)
                        <FieldHelp 
                            title="Exposure Notes" 
                            content={<><strong>💡 What to write (optional):</strong> Have you had any unique hands-on experiences? (e.g., "I helped my uncle fix cars" or "I run a small baking hustle").</>} 
                        />
                    </label>
                    <span className={`word-counter ${words > 15 || sentences > 1 ? 'warning' : 'success'}`}>
                        {words} words, {sentences} sent.
                    </span>
                </div>
                <textarea
                    className={`form-textarea ${errors?.['student_profile.interests_exposure.exposure_notes'] ? 'input-error' : ''}`}
                    placeholder="Briefly describe any relevant exposure (max 15 words, 1 sentence)..."
                    value={data.exposure_notes}
                    onChange={(e) => updateData({ exposure_notes: e.target.value })}
                />
                {errors?.['student_profile.interests_exposure.exposure_notes'] && (
                    <span className="field-error-text">{errors['student_profile.interests_exposure.exposure_notes']}</span>
                )}
            </div>
        </div>
    );
};

export default Step4Interests;
