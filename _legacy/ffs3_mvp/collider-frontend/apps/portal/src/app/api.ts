/**
 * Singleton API Client
 *
 * Creates a single instance of ColliderAPI for the Portal app.
 */
import { ColliderAPI, createColliderAPI } from '@collider-frontend/api-client';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

// Singleton instance
let apiInstance: ColliderAPI | null = null;

/**
 * Get the singleton API instance
 */
export function getAPI(): ColliderAPI {
  if (!apiInstance) {
    apiInstance = createColliderAPI({
      baseUrl: API_BASE,
    });
  }
  return apiInstance;
}

/**
 * Set the auth token on the API instance
 */
export function setAPIToken(token: string | undefined): void {
  getAPI().setToken(token);
}

/**
 * Export the API instance for direct use
 */
export const api = getAPI();

export default api;
