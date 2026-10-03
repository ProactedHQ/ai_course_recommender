import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { AlertTriangle } from 'lucide-react';
import Step1Grading from './steps/Step1Grading';
import Step2Personal from './steps/Step2Personal';
import Step3Practical from './steps/Step3Practical';
import Step4Interests from './steps/Step4Interests';
import Step5Influences from './steps/Step5Influences';
import Step6Priorities from './steps/Step6Priorities';
import PromptResult from '../PromptResult';
import { validateWizard } from '../../../utils/wizardValidation.js';
import { useAuth } from '../../../context/AuthContext';
import { apiFetch } from '../../../lib/apiClient';
import './Wizard.css';

const INITIAL_FORM_DATA = {
    student_profile: {
        kcse: {
            subjects: [
                { name: 'English', grade: '', _expectedGroup: 1 },
                { name: 'Kiswahili', grade: '', _expectedGroup: 1 },
                { name: 'Mathematics Alternative A', grade: '', _expectedGroup: 1 }
            ],
            custom_subjects: [],
            summary: { mean_grade: null, total_subjects: 0 }
        },
        personal_cognitive: {
            self_description: "",
            strengths: [],
            weaknesses: [],
            short_term_goals_1_3_years: [],
            long_term_goals_career: "",
            current_skills: { technical: [], soft: [] },
            preferred_learning_styles: [],
            career_aspirations: []
        },
        practical_factors: {
            time_hours_per_week: 0,
            budget_kes_estimate: 0,
            preferred_location: "",
            constraints_notes: ""
        },
        interests_exposure: {
            interests_hobbies: [],
            extracurriculars: [],
            exposure_notes: ""
        },
        influences: [],
        decision_priorities: {
            mode: "weights",
            items: [
                { key: "salary_potential", label: "Salary potential", weight: 20 },
                { key: "passion_interest", label: "Passion & interest", weight: 20 },
                { key: "job_stability", label: "Job stability", weight: 20 },
                { key: "work_life_balance", label: "Work-life balance", weight: 20 },
                { key: "social_impact", label: "Social impact", weight: 20 }
            ],
            total_weight: 100
        }
    }
};

const DRAFT_KEY = 'wizard_draft';

const WizardManager = ({ onComplete, isSubmitting, result, onRestart, submitError }) => {
    const [currentStep, setCurrentStep] = useState(1);
    const [loadingStepIndex, setLoadingStepIndex] = useState(0);
    const [isConfirmed, setIsConfirmed] = useState(false);
    const isInitialMount = useRef(true);
    const hasAttemptedSync = useRef(false);
    const [formData, setFormData] = useState(() => {
        // 🔄 Restore draft on mount (survives re-mounts from background re-verifications)
        try {
            const saved = sessionStorage.getItem(DRAFT_KEY);
            return saved ? JSON.parse(saved) : INITIAL_FORM_DATA;
        } catch {
            return INITIAL_FORM_DATA;
        }
    });
    const [submitAttempted, setSubmitAttempted] = useState(false);
    const [visitedSteps, setVisitedSteps] = useState(new Set());
    const { user, subscription, refreshAuth } = useAuth();

    // 💾 Save draft to sessionStorage whenever formData changes
    useEffect(() => {
        // Skip saving on the very first mount if we are about to sync from cloud
        if (isInitialMount.current) {
            isInitialMount.current = false;
            return;
        }

        try {
            sessionStorage.setItem(DRAFT_KEY, JSON.stringify(formData));
        } catch { /* storage full — silently ignore */ }
    }, [formData]);

    // ⏳ Simulated AI Loading Sequence
    useEffect(() => {
        if (!isSubmitting) {
            setLoadingStepIndex(0);
            return;
        }

        const loadingStepsCount = 7;
        const interval = setInterval(() => {
            setLoadingStepIndex(prev => {
                if (prev >= loadingStepsCount - 1) {
                    clearInterval(interval);
                    return prev;
                }
                return prev + 1;
            });
        }, 6500); // Change text roughly every 6.5 seconds

        return () => clearInterval(interval);
    }, [isSubmitting]);

    // 🔄 Deep Synchronization from History
    useEffect(() => {
        const syncFormFromCloud = async () => {
            if (!user || hasAttemptedSync.current) return;
            hasAttemptedSync.current = true;
            
            // Check if we already have a REAL local draft (not just the initial default)
            const localDraftRaw = sessionStorage.getItem(DRAFT_KEY);
            if (localDraftRaw) {
                try {
                    const parsed = JSON.parse(localDraftRaw);
                    // If it's more substantial than the initial default, don't overwrite
                    if (parsed.student_profile?.kcse?.subjects?.some(s => s.grade)) return;
                } catch { /* ignore parse error */ }
            }

            try {
                console.log("[Sync] Attempting to hydrate form from history...");
                const response = await apiFetch('/api/prompts/');
                const prompts = response?.results || response || [];
                
                if (Array.isArray(prompts) && prompts.length > 0) {
                    const latest = prompts[0];
                    const historicalProfile = latest?.payload?.student_profile;
                    
                    if (historicalProfile) {
                        console.log("[Sync] Found historical profile. Hydrating...");
                        setFormData(prev => ({
                            ...prev,
                            student_profile: {
                                ...prev.student_profile,
                                ...historicalProfile
                            }
                        }));
                        return; // Successfully hydrated from history
                    }
                }

                // Fallback: No history, try core profile pre-fill (KCSE subjects)
                console.log("[Sync] No history found. Falling back to core profile pre-fill.");
                // Backend route: course_recomeder_backend/urls.py -> StudentProfileViewSet.full
                const profileData = await apiFetch('/api/profile/');
                if (profileData?.academic_results?.length > 0) {
                    const sortedResults = [...profileData.academic_results].sort((a, b) => {
                        const score = (n) => n === 'English' ? 1 : n === 'Kiswahili' ? 2 : n.toLowerCase().includes('math') ? 3 : 99;
                        return score(a.name) - score(b.name);
                    });

                    const mappedSubjects = sortedResults.map(r => ({ name: r.name, grade: r.grade }));
                    
                    setFormData(prev => ({
                        ...prev,
                        student_profile: {
                            ...prev.student_profile,
                            kcse: {
                                ...prev.student_profile.kcse,
                                subjects: mappedSubjects
                            }
                        }
                    }));
                }
            } catch (err) {
                console.warn("[Sync] Error during form hydration:", err);
            }
        };

        syncFormFromCloud();
    }, [user]);

    const isLimitReached = useMemo(() => {
        // Scholar VVIP (unlimited) has remaining === null
        if (!user) return false; // Guest/Loading - let backend handle
        return subscription.remaining !== null && subscription.remaining <= 0;
    }, [user, subscription]);

    // Validation state
    const { isValid: isWizardValid, stepErrors, fieldErrors } = useMemo(() =>
        validateWizard(formData, isConfirmed),
        [formData, isConfirmed]);

    const totalSteps = 7;
    const stepNames = [
        "Academic",
        "Personal",
        "Practical",
        "Interests",
        "Influences",
        "Priorities",
        "Analysis"
    ];

    const handleNext = () => {
        setVisitedSteps(prev => new Set([...prev, currentStep]));
        
        // Lock progression if the current step has validation errors
        if (stepErrors[currentStep]) {
            return;
        }

        if (currentStep < totalSteps) {
            setCurrentStep(prev => Math.min(prev + 1, totalSteps));
        }
    };

    const handleBack = () => {
        if (currentStep > 1) setCurrentStep(prev => Math.max(prev - 1, 1));
    };

    const jumpToStep = (stepIdx) => {
        // Mark current step as visited before jumping to show any errors
        setVisitedSteps(prev => new Set([...prev, currentStep]));
        
        // Prevent jumping forward if the current step is incomplete/invalid
        if (stepIdx > currentStep && stepErrors[currentStep]) {
            return;
        }

        if (stepIdx === 7 && currentStep < 7) return;
        setCurrentStep(Math.max(1, Math.min(stepIdx, totalSteps)));
    };

    const updateProfileData = (section, newData) => {
        setFormData(prev => ({
            ...prev,
            student_profile: {
                ...prev.student_profile,
                [section]: {
                    ...prev.student_profile[section],
                    ...newData
                }
            }
        }));
    };

    const handleSubmit = async () => {
        setSubmitAttempted(true);
        // Mark all steps as visited on submit attempt
        setVisitedSteps(new Set([1, 2, 3, 4, 5, 6]));

        if (!isWizardValid) {
            return;
        }

        const payload = {
            version: "mvp_v1",
            student_profile: formData.student_profile,
            client_meta: {
                submitted_at: new Date().toISOString(),
                ui_language: "en",
                device: "web"
            }
        };
        const success = await onComplete(payload);
        if (success) {
            refreshAuth(); // Update prompt usage count
            setIsConfirmed(false);
            setSubmitAttempted(false);
            setVisitedSteps(new Set());
            setCurrentStep(7);
        }
    };

    const renderStep = () => {
        const profile = formData.student_profile;
        // Filter errors to only show those for visited steps
        const activeErrors = (stepNum) => (visitedSteps.has(stepNum) || submitAttempted) ? fieldErrors : {};

        switch (currentStep) {
            case 1: return <Step1Grading
                data={profile.kcse}
                updateData={(d) => updateProfileData('kcse', d)}
                errors={activeErrors(1)}
            />;
            case 2: return <Step2Personal
                data={profile.personal_cognitive}
                updateData={(d) => updateProfileData('personal_cognitive', d)}
                errors={activeErrors(2)}
            />;
            case 3: return <Step3Practical
                data={profile.practical_factors}
                updateData={(d) => updateProfileData('practical_factors', d)}
                errors={activeErrors(3)}
            />;
            case 4: return <Step4Interests
                data={profile.interests_exposure}
                updateData={(d) => updateProfileData('interests_exposure', d)}
                errors={activeErrors(4)}
            />;
            case 5: return <Step5Influences
                data={profile.influences}
                updateData={(d) => setFormData(prev => ({
                    ...prev,
                    student_profile: { ...prev.student_profile, influences: d }
                }))}
                errors={activeErrors(5)}
            />;
            case 6: return <Step6Priorities
                data={profile.decision_priorities}
                updateData={(d) => updateProfileData('decision_priorities', d)}
                isConfirmed={isConfirmed}
                onConfirmToggle={setIsConfirmed}
                errors={activeErrors(6)}
            />;
            case 7: return <div className="step-results-view">
                <PromptResult result={result} onRestart={() => {
                    onRestart();
                    setCurrentStep(1);
                    setVisitedSteps(new Set());
                    setSubmitAttempted(false);
                }} />
            </div>;
            default: return <div className="error-msg">Wizard Error: Invalid Step</div>;
        }
    };

    const progressPercentage = (currentStep / totalSteps) * 100;

    const loadingSteps = [
        "Analyzing your KCSE performance and subject strengths...",
        "Evaluating your cognitive profile and learning styles...",
        "Cross-referencing practical constraints and budget...",
        "Aligning your interests with emerging career trends...",
        "Weighting your decision priorities for optimal matching...",
        "Querying the knowledge graph for perfect academic fits...",
        "Finalizing your personalized academic blueprint..."
    ];

    return (
        <div className="wizard-container">
            {isSubmitting && (
                <div className="wizard-submitting-overlay">
                    <div className="wizard-loader-content">
                        <div className="premium-loader-rotating"></div>
                        <h3 className="loader-status-text">AI Analysis in Progress</h3>
                        <p className="loader-sub-text fade-in-text" key={loadingStepIndex}>
                            {loadingSteps[loadingStepIndex]}
                        </p>
                    </div>
                </div>
            )}
            <header className="wizard-header">
                {submitAttempted && !isWizardValid && (
                    <div className="wizard-global-error">
                        Please fix the highlighted steps before submitting.
                    </div>
                )}
                <div className="wizard-navigation-steps">
                    {stepNames.map((name, index) => {
                        const stepNum = index + 1;
                        const isInvalid = stepErrors[stepNum] === true;
                        const shouldShowInvalid = isInvalid && (visitedSteps.has(stepNum) || submitAttempted);
                        return (
                            <div
                                key={index}
                                className={`nav-step-item ${currentStep === stepNum ? 'active' : ''} ${shouldShowInvalid ? 'step-invalid' : ''}`}
                                onClick={() => jumpToStep(stepNum)}
                            >
                                <span className="nav-step-circle">{stepNum}</span>
                                <span className="nav-step-label">{name}</span>
                            </div>
                        );
                    })}
                </div>
                <div className="wizard-progress-bar">
                    <div className="progress-fill" style={{ width: `${progressPercentage}%` }}></div>
                </div>
            </header>

            <div className="wizard-body">
                <div className="wizard-step-content">
                    {renderStep()}
                </div>
            </div>

            {submitError && currentStep === 6 && (
                <div className="wizard-submit-error-wrapper">
                    <div className="wizard-submit-error">
                        <AlertTriangle size={18} className="wizard-error-icon" />
                        <span>{submitError}</span>
                    </div>
                </div>
            )}

            {currentStep <= 6 && (
                <footer className="wizard-footer">
                    <button
                        className="btn-back"
                        onClick={handleBack}
                        style={{ visibility: currentStep === 1 ? 'hidden' : 'visible' }}
                    >
                        Back
                    </button>

                    {currentStep < 6 ? (
                        <button
                            className={`btn-next${!stepErrors[currentStep] ? ' step-complete' : ''}`}
                            onClick={handleNext}
                        >Next Step</button>
                    ) : (
                        <div className="wizard-submit-group">
                            {isLimitReached && (
                                <p className="limit-warning-text">
                                    Limit reached. <a href="/app/subscription">Upgrade</a> for more.
                                </p>
                            )}
                            <button
                                className={`btn-submit ${(!isWizardValid || isLimitReached) ? 'opacity-50 cursor-not-allowed' : 'step-complete'}`}
                                onClick={handleSubmit}
                                disabled={isSubmitting || isLimitReached}
                            >
                                {isSubmitting ? 'Analyzing...' : isLimitReached ? 'Limit Reached' : 'Generate Recommendations'}
                            </button>
                        </div>
                    )}
                </footer>
            )}
        </div>
    );
};

export default WizardManager;
