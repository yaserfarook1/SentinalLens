import { useMsal } from "@azure/msal-react";
import { tokenRequest } from "@/lib/auth";
import { useCallback } from "react";

export function useAuth() {
  const { instance, accounts, inProgress } = useMsal();

  const isAuthenticated = accounts.length > 0;
  const isLoading = inProgress === "login" || inProgress === "acquire_token";

  const getAccessToken = useCallback(async (): Promise<string | null> => {
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
      console.error("Failed to acquire token:", error);
      return null;
    }
  }, [instance, accounts]);

  return {
    isAuthenticated,
    isLoading,
    accounts,
    instance,
    getAccessToken,
  };
}
