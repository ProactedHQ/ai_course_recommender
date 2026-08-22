import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { apiFetch } from '../lib/apiClient';
import { useAuth } from './AuthContext';

const PromptHistoryContext = createContext(null);

export const PromptHistoryProvider = ({ children }) => {
    const { user, session } = useAuth();
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    // Track which user's history we've already fetched — avoids refetch on token refresh
    const fetchedForUserRef = useRef(null);

    const fetchHistory = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await apiFetch('/api/prompts/');

            const formatted = data.map(item => {
                let title = 'New Recommendation';
                const dateObj = item.created_at ? new Date(item.created_at) : null;
                
                // Better placeholder title with timestamp to avoid duplicates in UI
                const timeStr = dateObj ? dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
                const dateStr = dateObj ? dateObj.toLocaleDateString([], { month: 'short', day: 'numeric' }) : '';
                const placeholder = `New Recommendation (${dateStr} ${timeStr})`.trim();

                if (item.result?.top_5?.[0]?.course) {
                    title = item.result.top_5[0].course;
                } else if (item.payload?.student_profile?.kcse?.summary?.mean_grade) {
                    title = `Grade: ${item.payload.student_profile.kcse.summary.mean_grade}`;
                } else {
                    title = placeholder;
                }

                return {
                    id: item.id,
                    title,
                    created_at: item.created_at, // Preserve for grouping logic
                    timestamp: dateObj ? dateObj.toLocaleDateString() : 'N/A',
                    status: item.result ? 'Completed' : 'Pending',
                    hasResult: !!item.result
                };
            });
            setHistory(formatted);
        } catch (err) {
            console.error('History fetch error:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    // 🔑 Key off user.id — NOT the session object.
    //    Supabase silently replaces the session object on every token refresh
    //    even though the user hasn't changed. Using user.id means we only
    //    re-fetch when the actual logged-in user changes (login / logout / switch).
    useEffect(() => {
        const userId = user?.id ?? null;

        if (userId && userId !== fetchedForUserRef.current) {
            // New user login — fetch once and remember
            fetchedForUserRef.current = userId;
            fetchHistory();
        } else if (!userId) {
            // Logged out — clear everything
            fetchedForUserRef.current = null;
            setHistory([]);
            setLoading(false);
            setError(null);
        }
        // If userId === fetchedForUserRef.current → same user, token refreshed silently → do nothing
    }, [user?.id, fetchHistory]);

    // Expose refreshHistory so components can request a fresh fetch after submission
    const refreshHistory = useCallback(async () => {
        if (user?.id) {
            await fetchHistory();
        }
    }, [user?.id, fetchHistory]);

    const deleteHistoryItem = useCallback(async (itemId) => {
        // Capture specific item for potential rollback if we want to be very precise,
        // but simple state snapshot is usually enough for history lists.
        let removedItem = null;

        setHistory(prev => {
            removedItem = prev.find(item => item.id === itemId);
            return prev.filter(item => item.id !== itemId);
        });

        try {
            // Background API call - NOT awaiting before UI update
            await apiFetch(`/api/prompts/${itemId}/`, { method: 'DELETE' });
            console.log(`Successfully soft-deleted item ${itemId} on server`);
        } catch (err) {
            console.error('Delete history error:', err);
            // Rollback if fail
            if (removedItem) {
                setHistory(prev => {
                    // Avoid duplicates if it was somehow re-added or re-fetched
                    if (prev.find(item => item.id === itemId)) return prev;
                    return [...prev, removedItem].sort((a, b) =>
                        new Date(b.created_at) - new Date(a.created_at)
                    );
                });
            }
        }
    }, []);

    return (
        <PromptHistoryContext.Provider value={{ history, loading, error, refreshHistory, deleteHistoryItem }}>
            {children}
        </PromptHistoryContext.Provider>
    );
};

export const usePromptHistory = () => {
    const context = useContext(PromptHistoryContext);
    if (!context) {
        throw new Error('usePromptHistory must be used within a PromptHistoryProvider');
    }
    return context;
};
