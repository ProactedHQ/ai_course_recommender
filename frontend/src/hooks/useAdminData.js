import { useState, useCallback, useRef } from 'react';
import adminApi from '../api/adminApi';

// Simple in-memory cache
const adminCache = new Map();
const CACHE_TTL = 60 * 1000; // 1 minute

export const useAdminData = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const timeoutRefs = useRef({});

    const fetchData = useCallback(async (key, apiCall, ...args) => {
        const cacheKey = `${key}_${JSON.stringify(args)}`;
        const cached = adminCache.get(cacheKey);

        // Return cached data if valid
        if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
            return cached.data;
        }

        try {
            setLoading(true);
            const data = await apiCall(...args);
            adminCache.set(cacheKey, { data, timestamp: Date.now() });
            return data;
        } catch (err) {
            console.error(`Admin cache fetch failed for ${key}:`, err);
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    const invalidateCache = useCallback((key) => {
        if (key) {
            for (const cacheKey of adminCache.keys()) {
                if (cacheKey.startsWith(key)) adminCache.delete(cacheKey);
            }
        } else {
            adminCache.clear();
        }
    }, []);

    return {
        fetchData,
        invalidateCache,
        loading,
        error
    };
};
