import axios from 'axios';
import { supabase } from '../lib/supabaseClient';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const getAuthHeaders = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return {
        "Content-Type": "application/json",
        "Authorization": session ? `Bearer ${session.access_token}` : ""
    };
};

const blogApi = {
    getStats: async (slug) => {
        const headers = await getAuthHeaders();
        return axios.get(`${API_BASE_URL}/api/blog/stats/${slug}/`, { headers });
    },
    toggleLike: async (slug) => {
        const headers = await getAuthHeaders();
        return axios.post(`${API_BASE_URL}/api/blog/like/${slug}/`, {}, { headers });
    },
    recordView: async (slug) => {
        const headers = await getAuthHeaders();
        return axios.post(`${API_BASE_URL}/api/blog/view/${slug}/`, {}, { headers });
    },
};

export default blogApi;
