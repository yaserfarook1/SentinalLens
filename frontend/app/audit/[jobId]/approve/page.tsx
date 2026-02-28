"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useMsal } from "@azure/msal-react";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useApi } from "@/hooks/useApi";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { Report } from "@/lib/types";

export default function ApprovePage() {
  const router = useRouter();
  const params = useParams();
  const jobId = params.jobId as string;
  const api = useApi();
  const { accounts } = useMsal();

  const [report, setReport] = useState<Report | null>(null);
  const [selectedTables, setSelectedTables] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        setIsLoading(true);
        const data = await api.getReport(jobId);
        setReport(data);
        // Pre-select all archive candidates
        const allArchives = new Set(
          data.archive_candidates.map((t) => t.table_name)
        );
        setSelectedTables(allArchives);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to fetch report"
        );
      } finally {
        setIsLoading(false);
      }
    };

    fetchReport();
  }, [jobId, api]);

  const toggleTable = (tableName: string) => {
    const next = new Set(selectedTables);
    if (next.has(tableName)) {
      next.delete(tableName);
    } else {
      next.add(tableName);
    }
    setSelectedTables(next);
  };

  const selectAll = () => {
    if (report) {
      const allArchives = new Set(
        report.archive_candidates.map((t) => t.table_name)
      );
      setSelectedTables(allArchives);
    }
  };

  const deselectAll = () => {
    setSelectedTables(new Set());
  };

  const calculateSavings = () => {
    if (!report) return 0;
    return report.archive_candidates
      .filter((t) => selectedTables.has(t.table_name))
      .reduce((sum, t) => sum + t.annual_savings, 0);
  };

  const handleApprove = async () => {
    if (selectedTables.size === 0) {
      setError("Please select at least one table to migrate");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      // This should trigger MFA if configured
      const response = await api.approveAudit(jobId, {
        job_id: jobId,
        selected_tables: Array.from(selectedTables),
      });

      setSuccess(
        `Migration approved! ID: ${response.migration_id}. ${response.approved_table_count} tables scheduled for migration.`
      );

      // Redirect after success
      setTimeout(() => {
        router.push("/dashboard");
      }, 2000);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to approve migration"
      );
      setIsSubmitting(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <ProtectedRoute>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">
            Approve Tier Migration
          </h1>
          <p className="text-gray-600 mt-1">
            Review and approve the recommended tier migrations
          </p>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center min-h-screen">
            <LoadingSpinner />
          </div>
        ) : error && !success ? (
          <div className="text-red-600 text-center py-8">{error}</div>
        ) : success ? (
          <Card className="border-green-200 bg-green-50">
            <CardContent className="pt-6 text-center">
              <div className="text-3xl mb-2">✓</div>
              <p className="text-green-800 font-semibold mb-2">{success}</p>
              <p className="text-green-700 text-sm">
                Redirecting to dashboard...
              </p>
            </CardContent>
          </Card>
        ) : report ? (
          <div className="space-y-6">
            {/* Warning */}
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
              <p className="text-amber-900 font-medium mb-1">
                ⚠️ This action requires approval
              </p>
              <p className="text-sm text-amber-800">
                You are signed in as <strong>{accounts?.[0]?.name}</strong>.
                Tier migrations require your security group membership and may
                trigger MFA verification.
              </p>
            </div>

            {/* Migration Summary */}
            <Card>
              <CardHeader>
                <CardTitle>Migration Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Total Tables</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">
                      {report.archive_candidates.length}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Selected</p>
                    <p className="text-2xl font-bold text-blue-600 mt-1">
                      {selectedTables.size}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Monthly Savings</p>
                    <p className="text-2xl font-bold text-green-600 mt-1">
                      {formatCurrency(calculateSavings() / 12)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Annual Savings</p>
                    <p className="text-2xl font-bold text-green-600 mt-1">
                      {formatCurrency(calculateSavings())}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Archive Candidates */}
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <CardTitle>Tables to Archive</CardTitle>
                  <div className="flex gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={selectAll}
                      className="text-xs"
                    >
                      Select All
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={deselectAll}
                      className="text-xs"
                    >
                      Deselect All
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {report.archive_candidates.map((table) => (
                    <label
                      key={table.table_name}
                      className="flex items-start gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={selectedTables.has(table.table_name)}
                        onChange={() => toggleTable(table.table_name)}
                        className="mt-1"
                      />
                      <div className="flex-1">
                        <div className="font-medium text-gray-900">
                          {table.table_name}
                        </div>
                        <div className="flex gap-2 mt-1">
                          <span className="text-xs text-gray-600">
                            {table.ingestion_gb_per_day.toFixed(2)} GB/day
                          </span>
                          <Badge variant="success" className="text-xs">
                            {table.confidence}
                          </Badge>
                          <span className="text-xs text-green-600 font-semibold ml-auto">
                            {formatCurrency(table.annual_savings)}/yr
                          </span>
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Action Buttons */}
            <div className="flex gap-4">
              <Button
                size="lg"
                onClick={handleApprove}
                disabled={
                  isSubmitting || selectedTables.size === 0 || !accounts?.length
                }
                className="flex-1 bg-green-600 hover:bg-green-700"
              >
                {isSubmitting ? "Approving..." : "Approve & Migrate"}
              </Button>
              <Button
                variant="secondary"
                size="lg"
                onClick={() => router.back()}
                disabled={isSubmitting}
                className="flex-1"
              >
                Cancel
              </Button>
            </div>

            {/* Info Box */}
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
              <strong>What happens next:</strong>
              <ul className="mt-2 list-disc list-inside space-y-1">
                <li>Selected tables will be moved to Archive tier</li>
                <li>Changes take effect within 24 hours</li>
                <li>Estimated savings will begin accruing immediately</li>
                <li>You can monitor migration status from Dashboard</li>
              </ul>
            </div>
          </div>
        ) : null}
      </div>
    </ProtectedRoute>
  );
}
