import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import WizardManager from '../../components/app/PromptWizard/WizardManager';
import PromptResult from '../../components/app/PromptResult';
import { apiFetch } from '../../lib/apiClient';
import { usePromptHistory } from '../../hooks/usePromptHistory';

const NewPrompt = () => {
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [result, setResult] = useState(null);
    const [submitError, setSubmitError] = useState(null);
    const { refreshHistory } = usePromptHistory();
    const location = useLocation();

    // 🔄 Reset state when navigating to /app/new (Fix for Sidebar "New Recommendation" button)
    useEffect(() => {
        if (location.pathname === '/app/new') {
            setResult(null);
            setSubmitError(null);
        }
    }, [location.pathname]);

    const handleWizardComplete = async (formData) => {
        setIsSubmitting(true);
        setSubmitError(null);

        try {
            const response = await apiFetch('/api/prompts/', {
                method: 'POST',
                body: { payload: formData }
            });

            // Log the complete response structure for debugging
            console.log('=== POST /api/prompts/ RESPONSE ===');
            console.log('Full response:', response);
            console.log('Path used (llm | fallback):', response.path_used);
            console.log('Recommendations object:', response.recommendations);
            console.log('Top 5 array:', response.recommendations?.top_5);
            console.log('First item:', response.recommendations?.top_5?.[0]);
            console.log('First item insight:', response.recommendations?.top_5?.[0]?.insight);
            console.log('====================================');

            // Validate response structure
            if (!response.recommendations) {
                throw new Error('No recommendations in response');
            }

            if (!response.recommendations.top_5 || !Array.isArray(response.recommendations.top_5)) {
                console.error('Invalid recommendations structure:', response.recommendations);
                throw new Error('Invalid recommendations format');
            }

            setResult(response.recommendations);
            await refreshHistory();
            return true; // Notify success
        } catch (err) {
            console.error('Submission error:', err);
            let rawMsg = err.message || '';
            let friendlyError = 'Our servers are currently busy. Please try again soon.';
            
            if (rawMsg.includes('Failed to fetch') || rawMsg.includes('NetworkError')) {
                friendlyError = 'Internet connection error. Please verify your network and try again.';
            } else if (rawMsg.includes('400') || rawMsg.includes('Validation')) {
                friendlyError = 'There was an issue processing your profile. Please check your answers and try again.';
            } else if (rawMsg.includes('429')) {
                friendlyError = 'Too many requests. Please wait a moment and try again.';
            } else if (rawMsg.includes('50') || rawMsg.includes('Technical')) {
                friendlyError = 'A technical error occurred on our end. Please try again shortly.';
            }

            setSubmitError(friendlyError);
            return false; // Notify failure
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleRestart = () => {
        setResult(null);
        setSubmitError(null);
    };

    return (
        <div className="new-prompt-page">
            <WizardManager
                onComplete={handleWizardComplete}
                isSubmitting={isSubmitting}
                result={result}
                onRestart={handleRestart}
                submitError={submitError}
            />
        </div>
    );
};

export default NewPrompt;
