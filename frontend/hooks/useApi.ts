import { useMsal } from "@azure/msal-react";
import { useCallback, useMemo } from "react";
import { createApiClient } from "@/lib/api-client";
import { tokenRequest } from "@/lib/auth";

export function useApi() {
  const { instance, accounts } = useMsal();

  const getToken = useCallback(async (): Promise<string | null> => {
    if (!accounts || accounts.length === 0) {
      return null;
    }

    try {
      const response = await instance.acquireTokenSilent({
        ...tokenRequest,
        account: accounts[0],
      });
      return response.accessToken;
    } catch (error) {
      // Token acquisition failed, user needs to login
      console.error("Failed to acquire token:", error);
      return null;
    }
  }, [instance, accounts]);

  const client = useMemo(() => createApiClient(getToken), [getToken]);

  return client;
}
