"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useApi } from "@/hooks/useApi";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { AuditJob } from "@/lib/types";

export default function HistoryPage() {
  const api = useApi();
  const [audits, setAudits] = useState<AuditJob[]>([]);
  const [filteredAudits, setFilteredAudits] = useState<AuditJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  useEffect(() => {
    const fetchAudits = async () => {
      try {
        setIsLoading(true);
        const data = await api.getAudits(100, 0);
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

  // Filter audits based on search and status
  useEffect(() => {
    let filtered = audits;

    if (searchTerm) {
      filtered = filtered.filter(
        (audit) =>
          audit.workspace_name
            .toLowerCase()
            .includes(searchTerm.toLowerCase()) ||
          audit.job_id.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (statusFilter !== "all") {
      filtered = filtered.filter((audit) => audit.status === statusFilter);
    }

    setFilteredAudits(filtered);
  }, [audits, searchTerm, statusFilter]);

  const formatCurrency = (value: number | undefined) => {
    if (!value) return "-";
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
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Audit History</h1>
          <p className="text-gray-600 mt-1">
            Search and filter all past audit runs
          </p>
        </div>

        {/* Search and Filter */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="Search workspace name or job ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Statuses</option>
                <option value="Completed">Completed</option>
                <option value="Running">Running</option>
                <option value="Queued">Queued</option>
                <option value="Failed">Failed</option>
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        <Card>
          <CardHeader>
            <CardTitle>
              Results ({filteredAudits.length} of {audits.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="py-12">
                <LoadingSpinner />
              </div>
            ) : error ? (
              <div className="text-red-600 py-4 text-center">{error}</div>
            ) : filteredAudits.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-600">
                  {audits.length === 0
                    ? "No audits found. Start your first audit from the Dashboard."
                    : "No audits match your search criteria."}
                </p>
                {audits.length === 0 && (
                  <Link href="/audit/new">
                    <Button className="mt-4">Create First Audit</Button>
                  </Link>
                )}
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
                        Job ID
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
                    {filteredAudits.map((audit) => (
                      <tr
                        key={audit.job_id}
                        className="border-b border-gray-100 hover:bg-gray-50"
                      >
                        <td className="px-4 py-3 text-gray-900">
                          {audit.workspace_name}
                        </td>
                        <td className="px-4 py-3 text-gray-600 text-sm font-mono">
                          {audit.job_id.slice(0, 8)}...
                        </td>
                        <td className="px-4 py-3 text-gray-600 text-sm">
                          {formatDate(audit.created_at)}
                        </td>
                        <td className="text-right px-4 py-3 text-gray-900">
                          {audit.tables_analyzed || "-"}
                        </td>
                        <td className="text-right px-4 py-3 font-semibold text-green-600">
                          {formatCurrency(audit.total_savings)}
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
                                View
                              </Button>
                            </Link>
                          )}
                          {audit.status === "Running" && (
                            <Link href={`/audit/${audit.job_id}/progress`}>
                              <Button variant="ghost" size="sm">
                                Monitor
                              </Button>
                            </Link>
                          )}
                          {audit.status === "Failed" && (
                            <span className="text-gray-500 text-sm">
                              {audit.error_message && (
                                <span title={audit.error_message}>Error</span>
                              )}
                            </span>
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
