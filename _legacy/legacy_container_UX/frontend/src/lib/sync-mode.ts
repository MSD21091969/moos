// Check if we are in cloud mode (VITE_API_URL is set and not empty)
export const isCloudMode = () => {
  return !!import.meta.env.VITE_API_URL;
};

/**
 * Generic wrapper to choose between Real API and Stubs based on environment.
 * 
 * @param realFn The actual API function to call in Cloud Mode
 * @param stubFn The stub function to call in Demo Mode
 * @param args Arguments to pass to the function
 */
export async function executeSync<T, A extends any[]>(
  realFn: (...args: A) => Promise<T>,
  stubFn: (...args: A) => Promise<T>,
  ...args: A
): Promise<T> {
  if (isCloudMode()) {
    try {
      console.log('[SyncMode] Executing Cloud API call...');
      return await realFn(...args);
    } catch (error) {
      console.error('[SyncMode] Cloud API call failed, falling back to stub if appropriate or rethrowing:', error);
      // Optional: Fallback logic could go here, but for now we want to know if cloud fails
      throw error;
    }
  } else {
    console.log('[SyncMode] Executing Demo Mode stub...');
    return await stubFn(...args);
  }
}
