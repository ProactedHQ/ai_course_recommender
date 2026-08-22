/**
 * Centralized validation logic for the AI Course Recommender wizard.
 */

export const countWords = (text) => {
    if (!text) return 0;
    return text.trim().split(/\s+/).filter(word => word.length > 0).length;
};

export const countSentences = (text) => {
    if (!text) return 0;
    // Simple sentence count: split by . ! or ?
    return text.split(/[.!?]+/).filter(sentence => sentence.trim().length > 0).length;
};

export const validateWizard = (formData, isConfirmed) => {
    const profile = formData?.student_profile;
    const fieldErrors = {};
    const stepErrors = { 1: false, 2: false, 3: false, 4: false, 5: false, 6: false };

    // --- STEP 1: ACADEMIC ---
    // Filter out completely empty rows (placeholders) so they don't block validation
    const subjects = (profile?.kcse?.subjects || []).filter(s => s.name || s.grade);
    
    if (subjects.length < 7) {
        fieldErrors['student_profile.kcse.subjects'] = `Please select at least 7 subjects (current: ${subjects.length}).`;
        stepErrors[1] = true;
    }

    // Uniqueness & Grades
    const names = subjects.map(s => s.name?.toLowerCase().trim() || '');
    subjects.forEach((s, idx) => {
        if (!s.grade) {
            fieldErrors[`student_profile.kcse.subjects.${idx}.grade`] = "Grade is required.";
            stepErrors[1] = true;
        }
        if (s.name && names.indexOf(s.name.toLowerCase().trim()) !== idx) {
            fieldErrors[`student_profile.kcse.subjects.${idx}.name`] = "Subject must be unique.";
            stepErrors[1] = true;
        }
    });

    // --- STEP 2: PERSONAL & COGNITIVE ---
    const personal = profile?.personal_cognitive;

    // Self Description: 40-200 words, >= 2 sentences
    const sdWords = countWords(personal?.self_description);
    const sdSentences = countSentences(personal?.self_description);
    if (!personal?.self_description || sdWords < 40) {
        fieldErrors['student_profile.personal_cognitive.self_description'] = "Write at least 40 words.";
        stepErrors[2] = true;
    } else if (sdSentences < 2) {
        fieldErrors['student_profile.personal_cognitive.self_description'] = "Write at least 2 sentences.";
        stepErrors[2] = true;
    } else if (sdWords > 200) {
        fieldErrors['student_profile.personal_cognitive.self_description'] = "Maximum 200 words.";
        stepErrors[2] = true;
    }

    // Required Sections (>= 1)
    const listFields = [
        { key: 'strengths', label: 'Strengths' },
        { key: 'weaknesses', label: 'Weaknesses' },
        { key: 'preferred_learning_styles', label: 'Learning styles' },
        { key: 'short_term_goals_1_3_years', label: 'Short-term goals' },
        { key: 'career_aspirations', label: 'Career aspirations' }
    ];

    listFields.forEach(f => {
        if (!personal?.[f.key] || personal[f.key].length === 0) {
            fieldErrors[`student_profile.personal_cognitive.${f.key}`] = `${f.label} are required.`;
            stepErrors[2] = true;
        }
    });

    // Skills
    if (!personal?.current_skills?.technical || personal.current_skills.technical.length === 0) {
        fieldErrors['student_profile.personal_cognitive.current_skills.technical'] = "Technical Skills are required.";
        stepErrors[2] = true;
    }
    if (!personal?.current_skills?.soft || personal.current_skills.soft.length === 0) {
        fieldErrors['student_profile.personal_cognitive.current_skills.soft'] = "Soft Skills are required.";
        stepErrors[2] = true;
    }

    // Long-term goals: >= 60 words
    const ltgWords = countWords(personal?.long_term_goals_career);
    if (!personal?.long_term_goals_career || ltgWords < 60) {
        fieldErrors['student_profile.personal_cognitive.long_term_goals_career'] = "Long-term goals must be at least 60 words.";
        stepErrors[2] = true;
    }

    // --- STEP 3: PRACTICAL ---
    const practical = profile?.practical_factors;
    if (!practical?.time_hours_per_week || practical.time_hours_per_week <= 0 || practical.time_hours_per_week > 168) {
        fieldErrors['student_profile.practical_factors.time_hours_per_week'] = "Study Time must be between 1 and 168 hours.";
        stepErrors[3] = true;
    }
    if (practical?.budget_kes_estimate === undefined || practical.budget_kes_estimate < 0) {
        fieldErrors['student_profile.practical_factors.budget_kes_estimate'] = "Budget Range must be >= 0.";
        stepErrors[3] = true;
    }
    if (!practical?.preferred_location) {
        fieldErrors['student_profile.practical_factors.preferred_location'] = "Preferred Location is required.";
        stepErrors[3] = true;
    }
    const cnWords = countWords(practical?.constraints_notes);
    if (cnWords > 30) {
        fieldErrors['student_profile.practical_factors.constraints_notes'] = "Constraint Notes: Maximum 30 words.";
        stepErrors[3] = true;
    }

    // --- STEP 4: INTERESTS & EXPOSURE ---
    const interests = profile?.interests_exposure;

    // Core Interests are required
    if (!interests?.interests_hobbies || interests.interests_hobbies.length === 0) {
        fieldErrors['student_profile.interests_exposure.interests_hobbies'] = "Please select at least one core interest.";
        stepErrors[4] = true;
    }

    const enWords = countWords(interests?.exposure_notes);
    const enSentences = countSentences(interests?.exposure_notes);
    if (enWords > 15) {
        fieldErrors['student_profile.interests_exposure.exposure_notes'] = "Exposure Notes: Maximum 15 words.";
        stepErrors[4] = true;
    } else if (enSentences > 1) {
        fieldErrors['student_profile.interests_exposure.exposure_notes'] = "Exposure Notes: Maximum 1 sentence.";
        stepErrors[4] = true;
    }

    // --- STEP 5: INFLUENCES ---
    const influences = profile?.influences || [];
    if (influences.length === 0) {
        fieldErrors['student_profile.influences'] = "At least one influence is required.";
        stepErrors[5] = true;
    }

    // --- STEP 6: PRIORITIES & CONFIRM ---
    const priorities = profile?.decision_priorities;
    if (Math.abs((priorities?.total_weight || 0) - 100) > 0.00001) {
        fieldErrors['student_profile.decision_priorities.total_weight'] = "Total weight must be exactly 100%.";
        stepErrors[6] = true;
    }
    if (!isConfirmed) {
        fieldErrors['confirmation'] = "You must confirm your preferences.";
        stepErrors[6] = true;
    }

    const isValid = !Object.values(stepErrors).some(err => err === true);

    return { isValid, stepErrors, fieldErrors };
};
