/**
 * MSAL Configuration and Authentication Utilities
 *
 * Initializes Azure AD (Entra ID) authentication using MSAL.js
 * for SentinelLens frontend.
 *
 * SECURITY:
 * - Client ID and Tenant ID are safe to expose (NEXT_PUBLIC_)
 * - No secrets stored in frontend code
 * - All tokens validated on backend before API calls
 */

import { PublicClientApplication, IPublicClientApplication } from "@azure/msal-browser";

// Ensure environment variables are set
const clientId = process.env.NEXT_PUBLIC_CLIENT_ID;
const tenantId = process.env.NEXT_PUBLIC_TENANT_ID;

if (!clientId) {
  throw new Error(
    "NEXT_PUBLIC_CLIENT_ID is not set. Please configure in .env.local"
  );
}

if (!tenantId) {
  throw new Error(
    "NEXT_PUBLIC_TENANT_ID is not set. Please configure in .env.local"
  );
}

const redirectUri = process.env.NEXT_PUBLIC_REDIRECT_URI || `${typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000'}/auth/redirect`;

/**
 * MSAL Configuration
 *
 * Configures:
 * - Client ID and Tenant ID from environment
 * - Redirect URI for auth callback
 * - Cache location (sessionStorage - cleared on browser close)
 * - Token request scopes
 */
const msalConfig = {
  auth: {
    clientId: clientId,
    authority: `https://login.microsoftonline.com/${tenantId}`,
    redirectUri: redirectUri,
    postLogoutRedirectUri: "/",
  },
  cache: {
    cacheLocation: "sessionStorage" as const,
    storeAuthStateInCookie: false,
  },
  system: {
    loggerOptions: {
      loggerCallback: (_level: any, message: string) => {
        if (process.env.NODE_ENV === "development") {
          console.log(`[MSAL] ${message}`);
        }
      },
      piiLoggingEnabled: false, // Never log PII
    },
  },
};

/**
 * Create MSAL PublicClientApplication instance
 *
 * This is the main authentication client used throughout the app.
 * Initialized once at module load time.
 */
let pca: IPublicClientApplication;

try {
  pca = new PublicClientApplication(msalConfig);
} catch (error) {
  console.error("[AUTH] Failed to initialize MSAL:", error);
  throw error;
}

/**
 * Token request configuration
 *
 * Requests access token for calling the backend API.
 * The 'scopes' array is specific to the app registration and API permissions.
 */
export const tokenRequest = {
  scopes: ["api://default/access_as_user"], // Default scope
  prompt: "select_account" as const,
};

/**
 * Login request configuration
 *
 * Configuration for initiating login flow (redirect or popup).
 * Uses same scopes as token request.
 */
export const loginRequest = {
  scopes: tokenRequest.scopes,
  prompt: "select_account" as const,
};

/**
 * Logout request configuration
 */
export const logoutRequest = {
  account: undefined,
  postLogoutRedirectUri: "/",
};

/**
 * Export MSAL instance for use in components
 */
export { pca };

/**
 * Get access token for API calls
 *
 * This function acquires an access token that should be sent
 * with API requests to the backend.
 *
 * The backend validates this token before processing requests.
 *
 * @returns Promise<string | null> - Access token or null if not authenticated
 */
export async function getAccessToken(): Promise<string | null> {
  try {
    const accounts = pca.getAllAccounts();
    if (accounts.length === 0) {
      return null;
    }

    const response = await pca.acquireTokenSilent({
      ...tokenRequest,
      account: accounts[0],
    });

    return response.accessToken;
  } catch (error) {
    console.error("[AUTH] Failed to get access token:", error);
    return null;
  }
}

/**
 * Check if user is authenticated
 *
 * @returns boolean - True if user has active account
 */
export function isAuthenticated(): boolean {
  return pca.getAllAccounts().length > 0;
}

/**
 * Get current authenticated user info
 *
 * @returns User info object or null if not authenticated
 */
export function getCurrentUser() {
  const accounts = pca.getAllAccounts();
  if (accounts.length === 0) {
    return null;
  }
  return accounts[0];
}

/**
 * Initiate login flow (redirect to Azure AD)
 */
export async function login() {
  try {
    await pca.loginPopup(loginRequest);
  } catch (error) {
    console.error("[AUTH] Login failed:", error);
    throw error;
  }
}

/**
 * Initiate logout
 */
export async function logout() {
  try {
    await pca.logout(logoutRequest);
  } catch (error) {
    console.error("[AUTH] Logout failed:", error);
    throw error;
  }
}
