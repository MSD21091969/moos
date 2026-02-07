/**
 * Environment helpers - centralized VITE_MODE access with proper trimming
 * Fixes issue where VITE_MODE may have trailing whitespace
 */

const rawMode = import.meta.env.VITE_MODE || 'development';
export const VITE_MODE = typeof rawMode === 'string' ? rawMode.trim() : 'development';

export const isDemoMode = (): boolean => VITE_MODE === 'demo';
export const isProductionMode = (): boolean => VITE_MODE === 'production';
export const isDevelopmentMode = (): boolean => VITE_MODE === 'development';

// Log once at startup for debugging
console.log(`🌍 Environment: VITE_MODE="${VITE_MODE}" (isDemoMode=${isDemoMode()})`);
