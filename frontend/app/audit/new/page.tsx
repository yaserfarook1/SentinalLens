"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useApi } from "@/hooks/useApi";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { Workspace } from "@/lib/types";

export default function NewAuditPage() {
  const router = useRouter();
  const api = useApi();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState<string>("");
  const [daysLookback, setDaysLookback] = useState<number>(30);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchWorkspaces = async () => {
      try {
        setIsLoading(true);
        const data = await api.getWorkspaces();
        setWorkspaces(data || []);
        if (data && data.length > 0) {
          setSelectedWorkspace(data[0].workspace_id);
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to fetch workspaces"
        );
      } finally {
        setIsLoading(false);
      }
    };

    fetchWorkspaces();
  }, [api]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!selectedWorkspace) {
      setError("Please select a workspace");
      return;
    }

    if (daysLookback < 1 || daysLookback > 365) {
      setError("Days lookback must be between 1 and 365");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      // Find the selected workspace object to get subscription_id
      const selectedWs = workspaces.find(ws => ws.workspace_id === selectedWorkspace);
      if (!selectedWs) {
        throw new Error("Selected workspace not found");
      }

      const job = await api.startAudit({
        workspace_id: selectedWorkspace,
        subscription_id: selectedWs.subscription_id,
        days_lookback: daysLookback,
      });

      // Redirect to progress page
      router.push(`/audit/${job.job_id}/progress`);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to start audit"
      );
      setIsSubmitting(false);
    }
  };

  return (
    <ProtectedRoute>
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">New Audit</h1>
          <p className="text-gray-600 mt-1">
            Configure and start a new cost optimization audit
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Audit Configuration</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="py-12">
                <LoadingSpinner />
              </div>
            ) : error && !isSubmitting ? (
              <div className="text-red-600 py-4 text-center">{error}</div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Workspace Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    Sentinel Workspace
                  </label>
                  <select
                    value={selectedWorkspace}
                    onChange={(e) => setSelectedWorkspace(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={isSubmitting}
                  >
                    <option value="">Select a workspace...</option>
                    {workspaces.map((ws) => (
                      <option key={ws.workspace_id} value={ws.workspace_id}>
                        {ws.workspace_name} ({ws.subscription_id})
                      </option>
                    ))}
                  </select>
                  <p className="mt-1 text-sm text-gray-500">
                    Select the Sentinel workspace to audit
                  </p>
                </div>

                {/* Days Lookback */}
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    Days Lookback
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="365"
                    value={daysLookback}
                    onChange={(e) => setDaysLookback(parseInt(e.target.value))}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={isSubmitting}
                  />
                  <p className="mt-1 text-sm text-gray-500">
                    Number of days to analyze (1-365 days, default 30)
                  </p>
                </div>

                {/* Error Message */}
                {error && isSubmitting && (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                    {error}
                  </div>
                )}

                {/* Info Box */}
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <h3 className="font-medium text-blue-900 mb-2">
                    What will be analyzed:
                  </h3>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• All Log Analytics tables in the workspace</li>
                    <li>• Ingestion volume for each table</li>
                    <li>• Analytics rules using each table</li>
                    <li>• Workbooks referencing tables</li>
                    <li>• Hunt queries and data connectors</li>
                    <li>• Potential savings from tier migrations</li>
                  </ul>
                </div>

                {/* Buttons */}
                <div className="flex gap-4">
                  <Button
                    type="submit"
                    size="lg"
                    disabled={isSubmitting || !selectedWorkspace}
                    className="flex-1 bg-blue-600 hover:bg-blue-700"
                  >
                    {isSubmitting ? "Starting Audit..." : "Start Audit"}
                  </Button>
                  <Button
                    type="button"
                    variant="secondary"
                    size="lg"
                    onClick={() => router.push("/dashboard")}
                    disabled={isSubmitting}
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                </div>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  );
}
