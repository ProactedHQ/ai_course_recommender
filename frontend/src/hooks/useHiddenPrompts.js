import { useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'hidden_prompt_ids';

/**
 * Hook to manage hidden prompt IDs in localStorage
 * Allows client-side hiding of prompts without backend deletion
 */
export function useHiddenPrompts() {
    const [hiddenIds, setHiddenIds] = useState(() => {
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            return stored ? JSON.parse(stored) : [];
        } catch (error) {
            console.error('Error loading hidden prompts:', error);
            return [];
        }
    });

    // Sync to localStorage whenever hiddenIds changes
    useEffect(() => {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(hiddenIds));
        } catch (error) {
            console.error('Error saving hidden prompts:', error);
        }
    }, [hiddenIds]);

    const hidePrompt = useCallback((promptId) => {
        setHiddenIds(prev => {
            if (prev.includes(promptId)) {
                return prev; // Already hidden
            }
            return [...prev, promptId];
        });
    }, []);

    const unhidePrompt = useCallback((promptId) => {
        setHiddenIds(prev => prev.filter(id => id !== promptId));
    }, []);

    const isHidden = useCallback((promptId) => {
        return hiddenIds.includes(promptId);
    }, [hiddenIds]);

    const clearAll = useCallback(() => {
        setHiddenIds([]);
    }, []);

    return {
        hiddenIds,
        hidePrompt,
        unhidePrompt,
        isHidden,
        clearAll
    };
}
