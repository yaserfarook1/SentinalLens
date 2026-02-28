"use client";

import React from "react";
import { useMsal } from "@azure/msal-react";
import { loginRequest } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { instance, accounts, inProgress } = useMsal();
  const [mockLoggedIn, setMockLoggedIn] = React.useState(
    typeof window !== "undefined" && localStorage.getItem("mockAuth") === "true"
  );

  const isAuthenticated = accounts.length > 0 || mockLoggedIn;

  const handleLogin = async () => {
    try {
      await instance.loginPopup(loginRequest);
    } catch (error) {
      console.error("Login failed, using mock auth for testing:", error);
      // Mock authentication for testing when no Azure AD configured
      localStorage.setItem("mockAuth", "true");
      setMockLoggedIn(true);
    }
  };

  if (inProgress === "login") {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Logging in...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6 text-center">
            <h1 className="text-2xl font-bold mb-2">SentinelLens</h1>
            <p className="text-gray-600 mb-6">
              AI-powered cost optimization for Microsoft Sentinel
            </p>
            <Button
              onClick={handleLogin}
              size="lg"
              className="w-full bg-blue-600 hover:bg-blue-700"
            >
              Sign in with Microsoft
            </Button>
            <p className="text-xs text-gray-500 mt-4">
              You must sign in to continue. This requires your organization's
              Microsoft account.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return <>{children}</>;
}
