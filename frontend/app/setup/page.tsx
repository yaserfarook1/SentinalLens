"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function SetupPage() {
  const router = useRouter();
  const [clientId, setClientId] = useState("");
  const [clientSecret, setClientSecret] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!clientId || !clientSecret) {
      setError("Both client ID and client secret are required");
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8002/api/v1";
      const response = await fetch(
        `${apiBaseUrl}/setup/credentials`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            client_id: clientId,
            client_secret: clientSecret,
          }),
        }
      );

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Failed to setup credentials");
      }

      const result = await response.json();
      setSuccess(true);

      // Redirect to dashboard after 2 seconds
      setTimeout(() => {
        router.push("/dashboard");
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to setup credentials");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xl">SL</span>
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">SentinelLens Setup</h1>
          <p className="text-gray-600 mt-2">
            Configure your Azure AD app registration credentials
          </p>
        </div>

        {/* Setup Card */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>App Registration Credentials</CardTitle>
          </CardHeader>
          <CardContent>
            {success ? (
              <div className="space-y-4">
                <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-green-800 font-medium">✓ Credentials configured successfully!</p>
                  <p className="text-green-700 text-sm mt-2">
                    The backend has been configured with your app registration.
                    Redirecting to dashboard...
                  </p>
                </div>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Instructions */}
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg space-y-3">
                  <h3 className="font-medium text-blue-900">How to get these credentials:</h3>
                  <ol className="text-sm text-blue-800 space-y-2 ml-4 list-decimal">
                    <li>Go to Azure Portal → Azure AD → App registrations</li>
                    <li>Find or create your app registration</li>
                    <li>Copy the <strong>Application (client) ID</strong></li>
                    <li>Go to Certificates & secrets → New client secret</li>
                    <li>Copy the <strong>secret value</strong> (not the ID)</li>
                  </ol>
                </div>

                {/* Client ID Input */}
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    Client ID (Application ID)
                  </label>
                  <input
                    type="text"
                    value={clientId}
                    onChange={(e) => setClientId(e.target.value)}
                    placeholder="12345678-1234-1234-1234-123456789012"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                    disabled={isLoading}
                  />
                  <p className="mt-1 text-sm text-gray-500">
                    Found in: Azure Portal → App registrations → Overview → Application (client) ID
                  </p>
                </div>

                {/* Client Secret Input */}
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    Client Secret
                  </label>
                  <input
                    type="password"
                    value={clientSecret}
                    onChange={(e) => setClientSecret(e.target.value)}
                    placeholder="••••••••••••••••••••••••"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                    disabled={isLoading}
                  />
                  <p className="mt-1 text-sm text-gray-500">
                    Found in: Azure Portal → App registrations → Certificates & secrets → Client secrets
                  </p>
                </div>

                {/* Error Message */}
                {error && (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-red-700 text-sm">
                      <strong>Error:</strong> {error}
                    </p>
                  </div>
                )}

                {/* Required Permissions Info */}
                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg space-y-2">
                  <h3 className="font-medium text-yellow-900">Required API Permissions:</h3>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="warning">Log Analytics Reader</Badge>
                    <Badge variant="warning">Tenant Reader</Badge>
                  </div>
                  <p className="text-sm text-yellow-800 mt-2">
                    Make sure your app registration has these permissions granted in Azure AD.
                  </p>
                </div>

                {/* Buttons */}
                <div className="flex gap-4 pt-4">
                  <Button
                    type="submit"
                    disabled={isLoading || !clientId || !clientSecret}
                    className="flex-1 bg-blue-600 hover:bg-blue-700"
                  >
                    {isLoading ? "Configuring..." : "Configure Credentials"}
                  </Button>
                  <Link href="/dashboard" className="flex-1">
                    <Button
                      type="button"
                      variant="secondary"
                      className="w-full"
                      disabled={isLoading}
                    >
                      Skip for Now
                    </Button>
                  </Link>
                </div>

                {/* Security Note */}
                <div className="p-3 bg-gray-100 rounded-lg">
                  <p className="text-xs text-gray-700">
                    <strong>Security Note:</strong> Your credentials are sent to the backend and saved in <code className="bg-gray-200 px-1 rounded">.env.local</code>.
                    Never commit this file to Git. In production, store credentials in Azure Key Vault.
                  </p>
                </div>
              </form>
            )}
          </CardContent>
        </Card>

        {/* Info Box */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">About This Setup</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p>
              <strong>What is an App Registration?</strong> It's a service principal that represents your application in Azure AD.
              This allows the backend to access Azure Sentinel and Log Analytics data on your behalf.
            </p>
            <p>
              <strong>Why do we need this?</strong> The app registration ensures that the backend authenticates as a trusted application,
              not as your personal user account. This provides better security and audit trails.
            </p>
            <p>
              <strong>What happens to my credentials?</strong> They're saved in <code className="bg-gray-100 px-1 rounded">.env.local</code>
              and used only by the backend. We recommend moving them to Azure Key Vault in production.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
