/**
 * useSSE Hook
 *
 * Manages Server-Sent Events connection for real-time updates.
 */
import { useState, useEffect, useRef, useCallback } from 'react';

export interface SSEEvent {
    type: string;
    data: unknown;
    timestamp: number;
}

export type SSEStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

export interface UseSSEOptions {
    /** SSE endpoint URL (null to disable) */
    url: string | null;
    /** Authorization token */
    token?: string;
    /** Auto-reconnect on disconnect */
    autoReconnect?: boolean;
    /** Reconnect delay in ms */
    reconnectDelay?: number;
    /** Max reconnect attempts */
    maxReconnectAttempts?: number;
    /** Event handler callback */
    onEvent?: (event: SSEEvent) => void;
    /** Error handler callback */
    onError?: (error: Error) => void;
}

export interface UseSSEResult {
    status: SSEStatus;
    lastEvent: SSEEvent | null;
    error: Error | null;
    disconnect: () => void;
    reconnect: () => void;
}

export function useSSE({
    url,
    token,
    autoReconnect = true,
    reconnectDelay = 3000,
    maxReconnectAttempts = 5,
    onEvent,
    onError,
}: UseSSEOptions): UseSSEResult {
    const [status, setStatus] = useState<SSEStatus>('disconnected');
    const [lastEvent, setLastEvent] = useState<SSEEvent | null>(null);
    const [error, setError] = useState<Error | null>(null);

    const eventSourceRef = useRef<EventSource | null>(null);
    const reconnectAttemptsRef = useRef(0);
    const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }

        if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
        }

        setStatus('disconnected');
    }, []);

    const connect = useCallback(() => {
        if (!url) return;

        disconnect();
        setStatus('connecting');
        setError(null);

        try {
            // Add token to URL if provided
            const sseUrl = token
                ? `${url}${url.includes('?') ? '&' : '?'}token=${encodeURIComponent(token)}`
                : url;

            const eventSource = new EventSource(sseUrl);
            eventSourceRef.current = eventSource;

            eventSource.onopen = () => {
                setStatus('connected');
                reconnectAttemptsRef.current = 0;
            };

            eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    const sseEvent: SSEEvent = {
                        type: data.type || 'message',
                        data: data.data || data,
                        timestamp: Date.now(),
                    };

                    setLastEvent(sseEvent);
                    onEvent?.(sseEvent);
                } catch (parseError) {
                    console.warn('[SSE] Failed to parse event:', event.data);
                }
            };

            eventSource.onerror = () => {
                setStatus('error');

                eventSource.close();
                eventSourceRef.current = null;

                const err = new Error('SSE connection error');
                setError(err);
                onError?.(err);

                // Auto-reconnect if enabled
                if (autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
                    reconnectAttemptsRef.current++;
                    console.log(`[SSE] Reconnecting (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`);

                    reconnectTimeoutRef.current = setTimeout(() => {
                        connect();
                    }, reconnectDelay);
                }
            };

            // Listen for specific event types
            eventSource.addEventListener('container_updated', (event) => {
                try {
                    const data = JSON.parse((event as MessageEvent).data);
                    const sseEvent: SSEEvent = {
                        type: 'container_updated',
                        data,
                        timestamp: Date.now(),
                    };
                    setLastEvent(sseEvent);
                    onEvent?.(sseEvent);
                } catch (parseError) {
                    console.warn('[SSE] Failed to parse container_updated event');
                }
            });

            eventSource.addEventListener('workflow_progress', (event) => {
                try {
                    const data = JSON.parse((event as MessageEvent).data);
                    const sseEvent: SSEEvent = {
                        type: 'workflow_progress',
                        data,
                        timestamp: Date.now(),
                    };
                    setLastEvent(sseEvent);
                    onEvent?.(sseEvent);
                } catch (parseError) {
                    console.warn('[SSE] Failed to parse workflow_progress event');
                }
            });

        } catch (err) {
            setStatus('error');
            setError(err instanceof Error ? err : new Error(String(err)));
            onError?.(err instanceof Error ? err : new Error(String(err)));
        }
    }, [url, token, autoReconnect, reconnectDelay, maxReconnectAttempts, onEvent, onError, disconnect, status]);

    const reconnect = useCallback(() => {
        reconnectAttemptsRef.current = 0;
        connect();
    }, [connect]);

    // Connect on mount / URL change
    useEffect(() => {
        if (url) {
            connect();
        } else {
            disconnect();
        }

        return () => {
            disconnect();
        };
    }, [url]); // Intentionally only depend on url

    return {
        status,
        lastEvent,
        error,
        disconnect,
        reconnect,
    };
}

export default useSSE;
