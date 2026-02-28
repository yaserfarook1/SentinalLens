"use client";

import React, { useEffect, useState } from "react";
import { MsalProvider } from "@azure/msal-react";
import { pca } from "@/lib/auth";
import { LoadingSpinner } from "@/components/ui/loading-spinner";

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    pca.initialize()
      .then(() => {
        setIsInitialized(true);
      })
      .catch((error) => {
        console.error("Failed to initialize MSAL:", error);
        setIsInitialized(true); // Still render, auth will handle it
      });
  }, []);

  if (!isInitialized) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return <MsalProvider instance={pca}>{children}</MsalProvider>;
}
