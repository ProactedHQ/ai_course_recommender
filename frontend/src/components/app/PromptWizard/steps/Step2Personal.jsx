import React, { useState } from 'react';
import { countWords } from '../../../../utils/wizardValidation.js';
import { HelpCircle } from 'lucide-react';
import FieldHelp from '../FieldHelp.jsx';

const Step2Personal = ({ data, updateData, errors }) => {
    const strengthsPool = ["Analytical thinking", "Creativity", "Leadership", "Discipline", "Curiosity", "Problem solving", "Communication", "Teamwork", "Resilience", "Attention to detail"];
    const weaknessesPool = ["Procrastination", "Poor time management", "Public speaking fear", "Low confidence", "Easily distracted", "Stress management", "Lack of focus"];
    const technicalPool = ["Basic computer use", "MS Word/Excel/PowerPoint", "Internet research", "Email writing", "Basic programming", "Graphic design basics"];
    const softPool = ["Communication", "Teamwork", "Adaptability", "Leadership", "Responsibility", "Critical thinking"];
    const learningStyles = [
        { id: 'visual', label: 'Visual', desc: 'Learn best with diagrams, videos, and charts.' },
        { id: 'auditory', label: 'Auditory', desc: 'Learn best with listening, discussion, and audio.' },
        { id: 'kinesthetic', label: 'Kinesthetic', desc: 'Learn best with hands-on practice and projects.' }
    ];

    const shortTermGoalsPool = [
        "Improve grades / study discipline",
        "Build a strong CV",
        "Learn a technical skill (coding/design/data)",
        "Improve communication skills",
        "Start a small business",
        "Get an internship / attachment",
        "Apply for scholarships",
        "Join a club / leadership role",
        "Prepare for university interviews",
        "Improve time management"
    ];

    const careerAspirationsPool = [
        "Software Engineer",
        "Data Scientist",
        "Cybersecurity Specialist",
        "Doctor / Clinical Officer",
        "Nurse",
        "Pharmacist",
        "Engineer (Civil/Electrical/Mechanical)",
        "Architect",
        "Teacher",
        "Lawyer",
        "Accountant",
        "Economist",
        "Pilot",
        "Journalist",
        "Graphic Designer",
        "Agronomist",
        "Business Owner / Entrepreneur"
    ];

    const [customGoal, setCustomGoal] = useState('');
    const [customAspiration, setCustomAspiration] = useState('');
    const [showOtherInput, setShowOtherInput] = useState(false);

    const toggleItem = (field, item, nestedField = null) => {
        let currentList = nestedField ? data[field][nestedField] : data[field];
        let newList;
        if (currentList.includes(item)) {
            newList = currentList.filter(i => i !== item);
        } else {
            newList = [...currentList, item];
        }

        if (nestedField) {
            updateData({ [field]: { ...data[field], [nestedField]: newList } });
        } else {
            updateData({ [field]: newList });
        }
    };

    const handleStyleToggle = (style) => {
        const isSelected = data.preferred_learning_styles.some(s => s.style === style.id);
        const newList = isSelected
            ? data.preferred_learning_styles.filter(s => s.style !== style.id)
            : [...data.preferred_learning_styles, { style: style.id, label: style.label, description: style.desc }];
        updateData({ preferred_learning_styles: newList });
    };

    const addCustomGoal = () => {
        if (customGoal.trim() && !data.short_term_goals_1_3_years.includes(customGoal.trim())) {
            updateData({ short_term_goals_1_3_years: [...data.short_term_goals_1_3_years, customGoal.trim()] });
            setCustomGoal('');
        }
    };

    const addCustomAspiration = () => {
        const trimmed = customAspiration.trim();
        if (trimmed && trimmed.split(/\s+/).length >= 2 && !data.career_aspirations.includes(trimmed)) {
            updateData({ career_aspirations: [...data.career_aspirations, trimmed] });
            setCustomAspiration('');
            setShowOtherInput(false);
        }
    };

    const sdWordCount = countWords(data.self_description);
    const ltgWordCount = countWords(data.long_term_goals_career);

    return (
        <div className="wizard-step">
            <h2 className="step-title">Personal & Cognitive</h2>
            <p className="step-description">Tell us about your strengths, skills, and how you learn best.</p>

            <div className="form-section">
                <div className="label-with-counter">
                    <label className="form-label">
                        Self Description <span className="required-asterisk">*</span>
                        <FieldHelp 
                            title="Self Description" 
                            content={<><strong>💡 What to write:</strong> Who are you outside of your grades? Write about your personality, what motivates you, or things you enjoy doing.<br/><br/><strong>Why it matters:</strong> The AI uses this to match you with a course and career environment where your true character will thrive.</>} 
                        />
                    </label>
                    <span className={`word-counter ${sdWordCount > 200 || sdWordCount < 40 ? 'warning' : 'success'}`}>
                        {sdWordCount} / 200 words
                    </span>
                </div>
                <textarea
                    className={`form-textarea ${errors?.['student_profile.personal_cognitive.self_description'] ? 'input-error' : ''}`}
                    placeholder="Describe yourself in a few sentences (min 40 words, max 200 words)..."
                    value={data.self_description}
                    onChange={(e) => updateData({ self_description: e.target.value })}
                />
                {errors?.['student_profile.personal_cognitive.self_description'] && (
                    <span className="field-error-text">{errors['student_profile.personal_cognitive.self_description']}</span>
                )}
            </div>

            <div className="form-section">
                <label className="form-label">
                    Strengths <span className="required-asterisk">*</span>
                    <FieldHelp 
                        title="Strengths" 
                        content={<><strong>💡 What to select:</strong> Things you are naturally good at.<br/><br/><strong>Why it matters:</strong> Certain careers demand specific strengths (e.g., Doctors need 'Resilience', Programmers need 'Analytical thinking').</>} 
                    />
                </label>
                <div className="chip-group">
                    {strengthsPool.map(item => (
                        <button
                            key={item}
                            className={`chip ${data.strengths.includes(item) ? 'active' : ''}`}
                            onClick={() => toggleItem('strengths', item)}
                        >
                            {item}
                        </button>
                    ))}
                </div>
                {errors?.['student_profile.personal_cognitive.strengths'] && (
                    <span className="field-error-text">{errors['student_profile.personal_cognitive.strengths']}</span>
                )}
            </div>

            <div className="form-section">
                <label className="form-label">
                    Weaknesses <span className="required-asterisk">*</span>
                    <FieldHelp 
                        title="Weaknesses" 
                        content={<><strong>💡 What to select:</strong> Areas where you struggle.<br/><br/><strong>Why it matters:</strong> Be absolutely honest! This helps the AI steer you away from careers where you might feel miserable or overwhelmed.</>} 
                    />
                </label>
                <div className="chip-group">
                    {weaknessesPool.map(item => (
                        <button
                            key={item}
                            className={`chip ${data.weaknesses.includes(item) ? 'active' : ''}`}
                            onClick={() => toggleItem('weaknesses', item)}
                        >
                            {item}
                        </button>
                    ))}
                </div>
                {errors?.['student_profile.personal_cognitive.weaknesses'] && (
                    <span className="field-error-text">{errors['student_profile.personal_cognitive.weaknesses']}</span>
                )}
            </div>

            <div className="form-grid">
                <div className="form-section">
                    <label className="form-label">
                        Technical Skills <span className="required-asterisk">*</span>
                        <FieldHelp 
                            title="Technical Skills" 
                            content={<><strong>💡 What to select:</strong> Hard, practical skills you already know.<br/><br/><strong>Why it matters:</strong> Gives you a great head-start if matched with courses requiring these basics.</>} 
                        />
                    </label>
                    <div className="chip-group">
                        {technicalPool.map(item => (
                            <button
                                key={item}
                                className={`chip ${data.current_skills.technical.includes(item) ? 'active' : ''}`}
                                onClick={() => toggleItem('current_skills', item, 'technical')}
                            >
                                {item}
                            </button>
                        ))}
                    </div>
                    {errors?.['student_profile.personal_cognitive.current_skills.technical'] && (
                        <span className="field-error-text">{errors['student_profile.personal_cognitive.current_skills.technical']}</span>
                    )}
                </div>
                <div className="form-section">
                    <label className="form-label">
                        Soft Skills <span className="required-asterisk">*</span>
                        <FieldHelp 
                            title="Soft Skills" 
                            content={<><strong>💡 What to select:</strong> How you handle people and situations.<br/><br/><strong>Why it matters:</strong> Many high-paying jobs care more about your soft skills than your technical ones.</>} 
                        />
                    </label>
                    <div className="chip-group">
                        {softPool.map(item => (
                            <button
                                key={item}
                                className={`chip ${data.current_skills.soft.includes(item) ? 'active' : ''}`}
                                onClick={() => toggleItem('current_skills', item, 'soft')}
                            >
                                {item}
                            </button>
                        ))}
                    </div>
                    {errors?.['student_profile.personal_cognitive.current_skills.soft'] && (
                        <span className="field-error-text">{errors['student_profile.personal_cognitive.current_skills.soft']}</span>
                    )}
                </div>
            </div>

            <div className="form-section">
                <label className="form-label">
                    Preferred Learning Styles <span className="required-asterisk">*</span>
                    <FieldHelp 
                        title="Preferred Learning Styles" 
                        content={<><strong>💡 What to select:</strong> How do you absorb information best in class?<br/><br/><strong>Why it matters:</strong> Some courses are very practical and hands-on, while others involve endless reading and listening.</>} 
                    />
                </label>
                <div className="learning-styles-grid">
                    {learningStyles.map(style => (
                        <div
                            key={style.id}
                            className={`style-card ${data.preferred_learning_styles.some(s => s.style === style.id) ? 'active' : ''} ${errors?.['student_profile.personal_cognitive.preferred_learning_styles'] ? 'input-error' : ''}`}
                            onClick={() => handleStyleToggle(style)}
                        >
                            <span className="style-label">{style.label}</span>
                            <span className="style-desc">{style.desc}</span>
                        </div>
                    ))}
                </div>
                {errors?.['student_profile.personal_cognitive.preferred_learning_styles'] && (
                    <span className="field-error-text">{errors['student_profile.personal_cognitive.preferred_learning_styles']}</span>
                )}
            </div>

            <div className="form-section">
                <label className="form-label">
                    Short-term Goals (1-3 years) <span className="required-asterisk">*</span>
                    <FieldHelp 
                        title="Short-term Goals" 
                        content={<><strong>💡 What to select:</strong> What do you want to achieve right after finishing high school or during your first campus years?<br/><br/><strong>Why it matters:</strong> Great goals act as stepping stones. The AI will recommend paths that make achieving these short-term goals easier.</>} 
                    />
                </label>
                <div className="chip-group">
                    {shortTermGoalsPool.map(item => (
                        <button
                            key={item}
                            className={`chip ${data.short_term_goals_1_3_years.includes(item) ? 'active' : ''}`}
                            onClick={() => toggleItem('short_term_goals_1_3_years', item)}
                        >
                            {item}
                        </button>
                    ))}
                </div>

                <div className="custom-input-group">
                    <input
                        type="text"
                        className="form-input"
                        placeholder="Add your own goal..."
                        value={customGoal}
                        onChange={(e) => setCustomGoal(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addCustomGoal())}
                    />
                    <button
                        type="button"
                        className="btn-add-custom"
                        onClick={addCustomGoal}
                        disabled={!customGoal.trim()}
                    >
                        Add
                    </button>
                </div>
                {errors?.['student_profile.personal_cognitive.short_term_goals_1_3_years'] && (
                    <span className="field-error-text">{errors['student_profile.personal_cognitive.short_term_goals_1_3_years']}</span>
                )}

                {data.short_term_goals_1_3_years.filter(g => !shortTermGoalsPool.includes(g)).length > 0 && (
                    <div className="custom-chips-section">
                        <span className="custom-chips-label">Your custom goals:</span>
                        <div className="chip-group">
                            {data.short_term_goals_1_3_years
                                .filter(g => !shortTermGoalsPool.includes(g))
                                .map(item => (
                                    <button
                                        key={item}
                                        className="chip active custom"
                                        onClick={() => toggleItem('short_term_goals_1_3_years', item)}
                                    >
                                        {item} <span className="remove-icon">×</span>
                                    </button>
                                ))}
                        </div>
                    </div>
                )}
            </div>

            <div className="form-section">
                <label className="form-label">
                    Career Aspirations <span className="required-asterisk">*</span>
                    <FieldHelp 
                        title="Career Aspirations" 
                        content={<><strong>💡 What to select:</strong> What jobs have you always dreamt of doing?<br/><br/><strong>Why it matters:</strong> This is your target destination. The AI will calculate the absolute best courses that will lead you precisely to these dream careers.</>} 
                    />
                </label>
                <div className="chip-group">
                    {careerAspirationsPool.map(item => (
                        <button
                            key={item}
                            className={`chip ${data.career_aspirations.includes(item) ? 'active' : ''}`}
                            onClick={() => toggleItem('career_aspirations', item)}
                        >
                            {item}
                        </button>
                    ))}

                    <button
                        className={`chip other-chip ${showOtherInput ? 'active' : ''}`}
                        onClick={() => setShowOtherInput(!showOtherInput)}
                    >
                        + Other
                    </button>
                </div>

                {showOtherInput && (
                    <div className="custom-input-group">
                        <input
                            type="text"
                            className="form-input"
                            placeholder="Type career (at least 2 words)..."
                            value={customAspiration}
                            onChange={(e) => setCustomAspiration(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addCustomAspiration())}
                            autoFocus
                        />
                        <button
                            type="button"
                            className="btn-add-custom"
                            onClick={addCustomAspiration}
                            disabled={!customAspiration.trim() || customAspiration.trim().split(/\s+/).length < 2}
                        >
                            Add
                        </button>
                    </div>
                )}
                {errors?.['student_profile.personal_cognitive.career_aspirations'] && (
                    <span className="field-error-text">{errors['student_profile.personal_cognitive.career_aspirations']}</span>
                )}

                {data.career_aspirations.filter(a => !careerAspirationsPool.includes(a)).length > 0 && (
                    <div className="custom-chips-section">
                        <span className="custom-chips-label">Your custom aspirations:</span>
                        <div className="chip-group">
                            {data.career_aspirations
                                .filter(a => !careerAspirationsPool.includes(a))
                                .map(item => (
                                    <button
                                        key={item}
                                        className="chip active custom"
                                        onClick={() => toggleItem('career_aspirations', item)}
                                    >
                                        {item} <span className="remove-icon">×</span>
                                    </button>
                                ))}
                        </div>
                    </div>
                )}
            </div>

            <div className="form-section">
                <div className="label-with-counter">
                    <label className="form-label">
                        Long-term Career Goals <span className="required-asterisk">*</span>
                        <FieldHelp 
                            title="Long-term Career Goals" 
                            content={<><strong>💡 What to write:</strong> Seriously imagine your life in 5-10 years. What role are you playing in society? Are you leading a team? Running your own firm? Solving climate change? Be descriptive.<br/><br/><strong>Why it matters:</strong> Your degree is just a tool to reach this exact vision. The richer your description, the more personalized your AI roadmap will be.</>} 
                        />
                    </label>
                    <span className={`word-counter ${ltgWordCount < 60 ? 'warning' : 'success'}`}>
                        {ltgWordCount} words (min 60)
                    </span>
                </div>
                <textarea
                    className={`form-textarea ${errors?.['student_profile.personal_cognitive.long_term_goals_career'] ? 'input-error' : ''}`}
                    placeholder="Where do you see yourself in 5-10 years? (min 60 words)"
                    value={data.long_term_goals_career}
                    onChange={(e) => updateData({ long_term_goals_career: e.target.value })}
                />
                {errors?.['student_profile.personal_cognitive.long_term_goals_career'] && (
                    <span className="field-error-text">{errors['student_profile.personal_cognitive.long_term_goals_career']}</span>
                )}
            </div>
        </div>
    );
};

export default Step2Personal;
