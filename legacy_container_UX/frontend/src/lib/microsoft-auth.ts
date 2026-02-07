import { PublicClientApplication, AccountInfo } from '@azure/msal-browser';

const msalConfig = {
  auth: {
    clientId: import.meta.env.VITE_AZURE_CLIENT_ID || 'f8c7976f-3e93-482e-9c9a-6f5c5c0e6e2e',
    authority: 'https://login.microsoftonline.com/common',
    redirectUri: window.location.origin,
  },
  cache: {
    cacheLocation: 'localStorage',
    storeAuthStateInCookie: false,
  },
};

export const msalInstance = new PublicClientApplication(msalConfig);

// Login scopes
export const loginRequest = {
  scopes: ['User.Read', 'Files.ReadWrite'],
};

// Initialize MSAL
export async function initializeMsal() {
  await msalInstance.initialize();
  await msalInstance.handleRedirectPromise();
}

// Login
export async function login() {
  try {
    const response = await msalInstance.loginPopup(loginRequest);
    return response.account;
  } catch (error) {
    console.error('Login failed:', error);
    throw error;
  }
}

// Logout
export async function logout() {
  await msalInstance.logoutPopup();
}

// Get current user
export function getCurrentUser(): AccountInfo | null {
  const accounts = msalInstance.getAllAccounts();
  return accounts.length > 0 ? accounts[0] : null;
}

// Get access token
export async function getAccessToken() {
  const account = getCurrentUser();
  if (!account) throw new Error('No user logged in');

  try {
    const response = await msalInstance.acquireTokenSilent({
      ...loginRequest,
      account,
    });
    return response.accessToken;
  } catch (error) {
    // Fallback to interactive login
    const response = await msalInstance.acquireTokenPopup(loginRequest);
    return response.accessToken;
  }
}
