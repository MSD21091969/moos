/**
 * useContainer Hook
 * 
 * Fetches and manages resolved container state for a node.
 */
import { useState, useEffect, useCallback } from 'react';
import type { ResolvedContainer } from './node-container';

export interface UseContainerOptions {
  appId: string;
  nodePath: string;
  apiBaseUrl?: string;
  token?: string;
}

export interface UseContainerResult {
  container: ResolvedContainer | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

export function useContainer({
  appId,
  nodePath,
  apiBaseUrl = 'http://localhost:8000/api/v1',
  token,
}: UseContainerOptions): UseContainerResult {
  const [container, setContainer] = useState<ResolvedContainer | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [fetchCount, setFetchCount] = useState(0);

  const refetch = useCallback(() => {
    setFetchCount((c) => c + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function fetchContainer() {
      setIsLoading(true);
      setError(null);

      try {
        const url = `${apiBaseUrl}/apps/${appId}/nodes/resolved?path=${encodeURIComponent(nodePath)}`;
        
        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
        };
        
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(url, { headers });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        
        if (!cancelled) {
          // The API returns { path, container, ancestry }
          setContainer(data.container || data);
          setIsLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error(String(err)));
          setIsLoading(false);
        }
      }
    }

    fetchContainer();

    return () => {
      cancelled = true;
    };
  }, [appId, nodePath, apiBaseUrl, token, fetchCount]);

  return {
    container,
    isLoading,
    error,
    refetch,
  };
}

export default useContainer;
