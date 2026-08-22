import { useState, useEffect } from 'react';
import { apiFetch } from '../lib/apiClient';

const CACHE_KEY = 'kcse_subjects';
const CACHE_DURATION = 7 * 24 * 60 * 60 * 1000; // 7 days in milliseconds

/**
 * Custom hook to fetch KCSE subjects from the backend API with localStorage caching.
 * Since subjects rarely change, we cache them locally to avoid repeated API calls.
 * 
 * @returns {{ subjects: Array, loading: boolean, error: string|null }}
 */
export const useSubjects = () => {
    const [subjects, setSubjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchSubjects = async () => {
            try {
                // Check localStorage for cached subjects
                const cachedData = localStorage.getItem(CACHE_KEY);

                if (cachedData) {
                    const { subjects: cachedSubjects, timestamp } = JSON.parse(cachedData);
                    const now = Date.now();

                    // If cache is still valid, use it
                    if (now - timestamp < CACHE_DURATION) {
                        setSubjects(cachedSubjects);
                        setLoading(false);
                        return;
                    }
                }

                // Cache miss or expired - fetch from API
                const data = await apiFetch('/api/subjects/');

                // Store in localStorage with timestamp
                localStorage.setItem(CACHE_KEY, JSON.stringify({
                    subjects: data,
                    timestamp: Date.now()
                }));

                setSubjects(data);
                setError(null);
            } catch (err) {
                console.error('Error fetching subjects:', err);
                setError(err.message || 'Failed to load subjects');

                // If fetch fails, try to use stale cache as fallback
                const cachedData = localStorage.getItem(CACHE_KEY);
                if (cachedData) {
                    const { subjects: cachedSubjects } = JSON.parse(cachedData);
                    setSubjects(cachedSubjects);
                    console.warn('Using stale cached subjects due to fetch error');
                }
            } finally {
                setLoading(false);
            }
        };

        fetchSubjects();
    }, []);

    return { subjects, loading, error };
};
