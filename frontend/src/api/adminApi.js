import axios from "axios";
import { supabase } from "../lib/supabaseClient";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// Helper to get auth headers
const getAuthHeaders = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${session?.access_token}`
    };
};

// Admin API functions
const adminApi = {
    // Get dashboard statistics
    async getStats() {
        const headers = await getAuthHeaders();
        const response = await axios.get(`${API_BASE_URL}/api/admin/analytics`, { headers });
        return response.data;
    },

    // Get all users with optional filters
    async getUsers(filters = {}) {
        const headers = await getAuthHeaders();
        const params = new URLSearchParams(filters).toString();
        const response = await axios.get(`${API_BASE_URL}/api/admin/users${params ? `?${params}` : ''}`, { headers });
        return response.data;
    },

    // Get single user details
    async getUserDetails(userId) {
        const headers = await getAuthHeaders();
        const response = await axios.get(`${API_BASE_URL}/api/admin/users/${userId}`, { headers });
        return response.data;
    },

    // Update user (subscription, status, etc.)
    async updateUser(userId, updates) {
        const headers = await getAuthHeaders();
        const response = await axios.patch(`${API_BASE_URL}/api/admin/users/${userId}`, updates, { headers });
        return response.data;
    },

    // Completely delete a user
    async deleteUser(userId) {
        const headers = await getAuthHeaders();
        const response = await axios.delete(`${API_BASE_URL}/api/admin/users/${userId}`, { headers });
        return response.data;
    },

    // Get recent activity logs
    async getActivityLogs(limit = 50) {
        const headers = await getAuthHeaders();
        const response = await axios.get(`${API_BASE_URL}/api/admin/chats?limit=${limit}`, { headers });
        return response.data;
    },

    // Get user activity logs
    async getUserActivity(userId, limit = 20) {
        const headers = await getAuthHeaders();
        const response = await axios.get(`${API_BASE_URL}/api/admin/users/${userId}/activity?limit=${limit}`, { headers });
        return response.data;
    },

    // Get analytics data
    async getAnalytics(period = '30d') {
        const headers = await getAuthHeaders();
        const response = await axios.get(`${API_BASE_URL}/api/admin/analytics?period=${period}`, { headers });
        return response.data;
    },

    // Impersonate user (get impersonation token)
    async impersonateUser(userId) {
        const headers = await getAuthHeaders();
        const response = await axios.post(`${API_BASE_URL}/api/admin/impersonate/${userId}`, {}, { headers });
        return response.data;
    },

    // Bulk update subscriptions
    async bulkUpdateSubscriptions(userIds, tier) {
        const headers = await getAuthHeaders();
        const response = await axios.post(`${API_BASE_URL}/api/admin/subscriptions/bulk`, { userIds, tier }, { headers });
        return response.data;
    },

    // Get Chat Logs (Prompt Submissions)
    async getChatLogs() {
        const headers = await getAuthHeaders();
        const response = await axios.get(`${API_BASE_URL}/api/admin/chats`, { headers });
        return response.data;
    },

    // Get Chat Detail
    async getChatDetails(id) {
        const headers = await getAuthHeaders();
        const response = await axios.get(`${API_BASE_URL}/api/admin/chats/${id}`, { headers });
        return response.data;
    }
};

export default adminApi;
