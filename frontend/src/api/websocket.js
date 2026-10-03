/**
 * WebSocket connector for AI Course Recommender frontend.
 *
 * NOTE: not imported anywhere at the moment. Production runs on cPanel Passenger
 * (WSGI), which cannot serve WebSockets, so recommendation progress is not streamed;
 * the app waits for the POST /api/prompts/ response instead.
 * Provides React hooks and utilities for WebSocket connections.
 *
 * Usage in React:
 *   import { useRecommendationWebSocket, useNotificationWebSocket } from './api/websocket';
 *
 *   function MyComponent() {
 *     const { status, recommendations, isConnected } = useRecommendationWebSocket();
 *     return (
 *       <div>
 *         {status && <p>{status.message} ({status.progress}%)</p>}
 *         {recommendations && <RecommendationList data={recommendations} />}
 *       </div>
 *     );
 *   }
 */
import { useState, useEffect, useRef } from 'react';

// WebSocket URL configuration
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';

/**
 * Create a WebSocket connection for recommendations
 * @param {function} onMessage - Callback for incoming messages
 * @param {function} onConnect - Callback when connected
 * @param {function} onError - Callback for errors
 * @returns {WebSocket} WebSocket instance
 */
export function connectRecommendationWS(onMessage, onConnect = null, onError = null) {
    const wsUrl = `${WS_BASE_URL}/ws/recommendations/`;
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        console.log('✅ WebSocket connected:', wsUrl);
        if (onConnect) onConnect();
    };

    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log('📨 WebSocket message:', data);
            if (onMessage) onMessage(data);
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    };

    socket.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        if (onError) onError(error);
    };

    socket.onclose = () => {
        console.log('🔌 WebSocket disconnected');
    };

    return socket;
}

/**
 * Create a WebSocket connection for notifications
 */
export function connectNotificationWS(onMessage, onConnect = null, onError = null) {
    const wsUrl = `${WS_BASE_URL}/ws/notifications/`;
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        console.log('✅ Notification WebSocket connected');
        if (onConnect) onConnect();
    };

    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log('🔔 Notification:', data);
            if (onMessage) onMessage(data);
        } catch (error) {
            console.error('Error parsing notification:', error);
        }
    };

    socket.onerror = (error) => {
        console.error('❌ Notification WebSocket error:', error);
        if (onError) onError(error);
    };

    socket.onclose = () => {
        console.log('🔌 Notification WebSocket disconnected');
    };

    return socket;
}

/**
 * React Hook for recommendation WebSocket
 * 
 * @returns {{
 *   status: {message: string, progress: number} | null,
 *   recommendations: object | null,
 *   isConnected: boolean,
 *   error: Error | null
 * }}
 */
export function useRecommendationWebSocket() {
    const [status, setStatus] = useState(null);
    const [recommendations, setRecommendations] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    const [error, setError] = useState(null);
    const socketRef = useRef(null);

    useEffect(() => {
        // Connect to WebSocket
        const socket = connectRecommendationWS(
            (data) => {
                switch (data.type) {
                    case 'connection_established':
                        setIsConnected(true);
                        break;

                    case 'recommendation_status':
                        setStatus({
                            message: data.message,
                            progress: data.progress,
                            status: data.status
                        });
                        break;

                    case 'recommendation_complete':
                        setRecommendations(data.recommendations);
                        setStatus({
                            message: 'Complete!',
                            progress: 100,
                            status: 'complete'
                        });
                        break;

                    default:
                        console.log('Unknown message type:', data.type);
                }
            },
            () => setIsConnected(true),
            (err) => setError(err)
        );

        socketRef.current = socket;

        // Cleanup on unmount
        return () => {
            if (socketRef.current) {
                socketRef.current.close();
            }
        };
    }, []);

    return { status, recommendations, isConnected, error };
}

/**
 * React Hook for notification WebSocket
 */
export function useNotificationWebSocket() {
    const [notifications, setNotifications] = useState([]);
    const [isConnected, setIsConnected] = useState(false);
    const socketRef = useRef(null);

    useEffect(() => {
        const socket = connectNotificationWS(
            (data) => {
                if (data.type === 'system_notification' || data.type === 'user_notification') {
                    setNotifications(prev => [data, ...prev]);
                }
            },
            () => setIsConnected(true)
        );

        socketRef.current = socket;

        return () => {
            if (socketRef.current) {
                socketRef.current.close();
            }
        };
    }, []);

    const clearNotifications = () => setNotifications([]);

    return { notifications, isConnected, clearNotifications };
}
