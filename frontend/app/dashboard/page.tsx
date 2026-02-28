"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useApi } from "@/hooks/useApi";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { AuditJob } from "@/lib/types";
import Link from "next/link";

export default function DashboardPage() {
  const router = useRouter();
  const api = useApi();
  const [audits, setAudits] = useState<AuditJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAudits = async () => {
      try {
        setIsLoading(true);
        const data = await api.getAudits(50, 0);
        setAudits(data || []);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to fetch audits"
        );
      } finally {
        setIsLoading(false);
      }
    };

    fetchAudits();
  }, [api]);

  const totalSavings = audits.reduce((sum, audit) => sum + (audit.total_savings || 0), 0);
  const averageTables = audits.length > 0 ? Math.round(audits.reduce((sum, audit) => sum + (audit.tables_analyzed || 0), 0) / audits.length) : 0;
  const completedCount = audits.filter((a) => a.status === "Completed").length;

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Completed":
        return "bg-green-100 text-green-800";
      case "Failed":
        return "bg-red-100 text-red-800";
      case "Running":
        return "bg-blue-100 text-blue-800";
      case "Queued":
        return "bg-yellow-100 text-yellow-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <ProtectedRoute>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600 mt-1">
              Monitor your Sentinel cost optimization audits
            </p>
          </div>
          <Link href="/audit/new">
            <Button size="lg" className="bg-blue-600 hover:bg-blue-700">
              New Audit
            </Button>
          </Link>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <p className="text-sm text-gray-600 font-medium">Total Saved YTD</p>
                <p className="text-3xl font-bold text-green-600 mt-2">
                  {formatCurrency(totalSavings)}
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <p className="text-sm text-gray-600 font-medium">Avg Tables/Audit</p>
                <p className="text-3xl font-bold text-blue-600 mt-2">
                  {averageTables}
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <p className="text-sm text-gray-600 font-medium">Success Rate</p>
                <p className="text-3xl font-bold text-purple-600 mt-2">
                  {audits.length > 0 ? Math.round((completedCount / audits.length) * 100) : 0}%
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Audits Table */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Audits</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="py-12">
                <LoadingSpinner />
              </div>
            ) : error ? (
              <div className="text-red-600 py-4 text-center">{error}</div>
            ) : audits.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-600 mb-4">No audits yet</p>
                <Link href="/audit/new">
                  <Button>Start Your First Audit</Button>
                </Link>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left px-4 py-3 font-semibold text-gray-900">
                        Workspace
                      </th>
                      <th className="text-left px-4 py-3 font-semibold text-gray-900">
                        Date
                      </th>
                      <th className="text-right px-4 py-3 font-semibold text-gray-900">
                        Tables
                      </th>
                      <th className="text-right px-4 py-3 font-semibold text-gray-900">
                        Savings
                      </th>
                      <th className="text-left px-4 py-3 font-semibold text-gray-900">
                        Status
                      </th>
                      <th className="text-right px-4 py-3 font-semibold text-gray-900">
                        Action
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {audits.map((audit) => (
                      <tr
                        key={audit.job_id}
                        className="border-b border-gray-100 hover:bg-gray-50"
                      >
                        <td className="px-4 py-3 text-gray-900">
                          {audit.workspace_name}
                        </td>
                        <td className="px-4 py-3 text-gray-600 text-sm">
                          {formatDate(audit.created_at)}
                        </td>
                        <td className="text-right px-4 py-3 text-gray-900">
                          {audit.tables_analyzed || "-"}
                        </td>
                        <td className="text-right px-4 py-3 font-semibold text-green-600">
                          {audit.total_savings ? formatCurrency(audit.total_savings) : "-"}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(
                              audit.status
                            )}`}
                          >
                            {audit.status}
                          </span>
                        </td>
                        <td className="text-right px-4 py-3">
                          {audit.status === "Completed" && (
                            <Link href={`/audit/${audit.job_id}/report`}>
                              <Button variant="ghost" size="sm">
                                View Report
                              </Button>
                            </Link>
                          )}
                          {audit.status === "Running" && (
                            <Link href={`/audit/${audit.job_id}/progress`}>
                              <Button variant="ghost" size="sm">
                                View Progress
                              </Button>
                            </Link>
                          )}
                          {(audit.status === "Queued" ||
                            audit.status === "Failed") && (
                            <span className="text-gray-500 text-sm">-</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  );
}
