import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiFetch } from '../../lib/apiClient';
import PromptResult from '../../components/app/PromptResult';
import './HistoryDetail.css';

const HistoryDetail = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [submission, setSubmission] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchDetail = async () => {
            setLoading(true);
            try {
                const data = await apiFetch(`/api/prompts/${id}/`);

                // Log response for debugging
                console.log('=== GET /api/prompts/:id RESPONSE ===');
                console.log('Submission:', data);
                console.log('Result:', data.result);
                console.log('Result top_5:', data.result?.top_5);
                console.log('======================================');

                // Validate result exists
                if (!data.result) {
                    console.warn('No result found for submission:', id);
                    throw new Error('No recommendation data found for this submission');
                }

                setSubmission(data);
            } catch (err) {
                console.error('Fetch history detail error:', err);
                setError(err.message || 'Failed to load this recommendation history.');
            } finally {
                setLoading(false);
            }
        };
        fetchDetail();
    }, [id]);

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center p-20 text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-teal-500 mb-4"></div>
                <p>Loading details...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-10 text-center">
                <p className="text-red-500 mb-4">{error}</p>
                <button onClick={() => navigate('/app/history')} className="btn-back">Go back to history</button>
            </div>
        );
    }

    return (
        <div className="history-detail-page">
            {/* Header removed for cleaner UI as requested */}

            <PromptResult result={submission.result} onRestart={() => navigate('/app/new')} />
        </div>
    );
};

export default HistoryDetail;
