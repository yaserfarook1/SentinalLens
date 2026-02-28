"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useApi } from "@/hooks/useApi";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { Report, TableRecommendation } from "@/lib/types";
import Link from "next/link";

export default function ReportPage() {
  const router = useRouter();
  const params = useParams();
  const jobId = params.jobId as string;
  const api = useApi();

  const [report, setReport] = useState<Report | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        setIsLoading(true);
        const data = await api.getReport(jobId);
        setReport(data);
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

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const getConfidenceColor = (confidence: string) => {
    switch (confidence) {
      case "HIGH":
        return "success";
      case "MEDIUM":
        return "warning";
      case "LOW":
        return "danger";
      default:
        return "default";
    }
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case "Hot":
        return "danger";
      case "Basic":
        return "warning";
      case "Archive":
        return "success";
      default:
        return "default";
    }
  };

  const TableRow = ({ table, isArchive }: { table: TableRecommendation; isArchive?: boolean }) => (
    <tr className="border-b border-gray-100 hover:bg-gray-50">
      <td className="px-4 py-3 font-medium text-gray-900">{table.table_name}</td>
      <td className="px-4 py-3">
        <Badge variant={getTierColor(table.current_tier)}>
          {table.current_tier}
        </Badge>
      </td>
      <td className="px-4 py-3 text-right text-gray-600">
        {table.ingestion_gb_per_day.toFixed(2)} GB/day
      </td>
      <td className="px-4 py-3 text-right text-gray-600">
        {table.rule_coverage_count}
      </td>
      <td className="px-4 py-3">
        <Badge variant={getConfidenceColor(table.confidence)}>
          {table.confidence}
        </Badge>
      </td>
      <td className="px-4 py-3 text-right font-semibold text-green-600">
        {formatCurrency(table.annual_savings)}
      </td>
      {isArchive && (
        <td className="px-4 py-3 text-right">
          <Button variant="ghost" size="sm">
            Select
          </Button>
        </td>
      )}
    </tr>
  );

  return (
    <ProtectedRoute>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isLoading ? (
          <div className="flex items-center justify-center min-h-screen">
            <LoadingSpinner />
          </div>
        ) : error ? (
          <div className="text-red-600 text-center py-8">{error}</div>
        ) : report ? (
          <>
            {/* Header */}
            <div className="flex justify-between items-start mb-6">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Audit Report
                </h1>
                <p className="text-gray-600 mt-1">
                  {report.workspace_name} •{" "}
                  {new Date(report.timestamp).toLocaleDateString()}
                </p>
              </div>
              <div className="flex gap-2">
                <Button variant="secondary" size="sm">
                  Download JSON
                </Button>
                <Button variant="secondary" size="sm">
                  Download PDF
                </Button>
                <Link href={`/audit/${jobId}/approve`}>
                  <Button size="sm" className="bg-green-600 hover:bg-green-700">
                    Approve & Migrate
                  </Button>
                </Link>
              </div>
            </div>

            {/* Executive Summary */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center">
                    <p className="text-sm text-gray-600 font-medium">
                      Tables Analyzed
                    </p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">
                      {report.summary.total_tables_analyzed}
                    </p>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="text-center">
                    <p className="text-sm text-gray-600 font-medium">
                      Archive Candidates
                    </p>
                    <p className="text-3xl font-bold text-red-600 mt-2">
                      {report.archive_candidates.length}
                    </p>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="text-center">
                    <p className="text-sm text-gray-600 font-medium">
                      Monthly Savings
                    </p>
                    <p className="text-3xl font-bold text-green-600 mt-2">
                      {formatCurrency(report.summary.total_monthly_savings)}
                    </p>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="text-center">
                    <p className="text-sm text-gray-600 font-medium">
                      Annual Savings
                    </p>
                    <p className="text-3xl font-bold text-blue-600 mt-2">
                      {formatCurrency(report.summary.total_annual_savings)}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Detailed Analysis */}
            <Card className="mb-8">
              <CardHeader>
                <CardTitle>Detailed Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="archive" className="w-full">
                  <TabsList>
                    <TabsTrigger value="archive">
                      Archive Candidates ({report.archive_candidates.length})
                    </TabsTrigger>
                    <TabsTrigger value="low-usage">
                      Low Usage ({report.low_usage_candidates.length})
                    </TabsTrigger>
                    <TabsTrigger value="active">
                      Active ({report.active_tables.length})
                    </TabsTrigger>
                    <TabsTrigger value="warnings">
                      Warnings ({report.warnings.length})
                    </TabsTrigger>
                  </TabsList>

                  {/* Archive Candidates */}
                  <TabsContent value="archive" className="mt-6">
                    {report.archive_candidates.length === 0 ? (
                      <p className="text-gray-600 text-center py-8">
                        No archive candidates found
                      </p>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full">
                          <thead>
                            <tr className="border-b border-gray-200">
                              <th className="text-left px-4 py-3 font-semibold text-gray-900">
                                Table Name
                              </th>
                              <th className="text-left px-4 py-3 font-semibold text-gray-900">
                                Current Tier
                              </th>
                              <th className="text-right px-4 py-3 font-semibold text-gray-900">
                                Ingestion
                              </th>
                              <th className="text-right px-4 py-3 font-semibold text-gray-900">
                                Rules
                              </th>
                              <th className="text-left px-4 py-3 font-semibold text-gray-900">
                                Confidence
                              </th>
                              <th className="text-right px-4 py-3 font-semibold text-gray-900">
                                Annual Savings
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {report.archive_candidates.map((table) => (
                              <TableRow
                                key={table.table_name}
                                table={table}
                                isArchive
                              />
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </TabsContent>

                  {/* Low Usage */}
                  <TabsContent value="low-usage" className="mt-6">
                    {report.low_usage_candidates.length === 0 ? (
                      <p className="text-gray-600 text-center py-8">
                        No low usage tables found
                      </p>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full">
                          <thead>
                            <tr className="border-b border-gray-200">
                              <th className="text-left px-4 py-3 font-semibold text-gray-900">
                                Table Name
                              </th>
                              <th className="text-left px-4 py-3 font-semibold text-gray-900">
                                Current Tier
                              </th>
                              <th className="text-right px-4 py-3 font-semibold text-gray-900">
                                Ingestion
                              </th>
                              <th className="text-right px-4 py-3 font-semibold text-gray-900">
                                Rules
                              </th>
                              <th className="text-left px-4 py-3 font-semibold text-gray-900">
                                Confidence
                              </th>
                              <th className="text-right px-4 py-3 font-semibold text-gray-900">
                                Annual Savings
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {report.low_usage_candidates.map((table) => (
                              <TableRow key={table.table_name} table={table} />
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </TabsContent>

                  {/* Active Tables */}
                  <TabsContent value="active" className="mt-6">
                    {report.active_tables.length === 0 ? (
                      <p className="text-gray-600 text-center py-8">
                        No active tables
                      </p>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full">
                          <thead>
                            <tr className="border-b border-gray-200">
                              <th className="text-left px-4 py-3 font-semibold text-gray-900">
                                Table Name
                              </th>
                              <th className="text-left px-4 py-3 font-semibold text-gray-900">
                                Current Tier
                              </th>
                              <th className="text-right px-4 py-3 font-semibold text-gray-900">
                                Ingestion
                              </th>
                              <th className="text-right px-4 py-3 font-semibold text-gray-900">
                                Rules
                              </th>
                              <th className="text-left px-4 py-3 font-semibold text-gray-900">
                                Status
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {report.active_tables.map((table) => (
                              <tr
                                key={table.table_name}
                                className="border-b border-gray-100 hover:bg-gray-50"
                              >
                                <td className="px-4 py-3 font-medium text-gray-900">
                                  {table.table_name}
                                </td>
                                <td className="px-4 py-3">
                                  <Badge variant={getTierColor(table.current_tier)}>
                                    {table.current_tier}
                                  </Badge>
                                </td>
                                <td className="px-4 py-3 text-right text-gray-600">
                                  {table.ingestion_gb_per_day.toFixed(2)} GB/day
                                </td>
                                <td className="px-4 py-3 text-right text-gray-600">
                                  {table.rule_coverage_count}
                                </td>
                                <td className="px-4 py-3">
                                  <Badge variant="success">Keep</Badge>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </TabsContent>

                  {/* Warnings */}
                  <TabsContent value="warnings" className="mt-6">
                    {report.warnings.length === 0 ? (
                      <p className="text-gray-600 text-center py-8">
                        No warnings
                      </p>
                    ) : (
                      <div className="space-y-4">
                        {report.warnings.map((warning, idx) => (
                          <div
                            key={idx}
                            className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg"
                          >
                            <div className="flex gap-3">
                              <span className="text-xl">⚠️</span>
                              <div className="flex-1">
                                <p className="font-semibold text-yellow-900">
                                  {warning.warning_type} - {warning.table_name}
                                </p>
                                <p className="text-yellow-800 text-sm mt-1">
                                  {warning.description}
                                </p>
                                <p className="text-yellow-700 text-sm mt-2 font-medium">
                                  Recommendation: {warning.recommendation}
                                </p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>

            {/* Metadata */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Audit Metadata</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600">Parse Success Rate</p>
                    <p className="font-semibold text-gray-900 mt-1">
                      {Math.round(report.metadata.kql_parsing_success_rate * 100)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-600">Tables Analyzed</p>
                    <p className="font-semibold text-gray-900 mt-1">
                      {report.metadata.tables_analyzed}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-600">Rules Analyzed</p>
                    <p className="font-semibold text-gray-900 mt-1">
                      {report.metadata.rules_analyzed}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-600">Workbooks Analyzed</p>
                    <p className="font-semibold text-gray-900 mt-1">
                      {report.metadata.workbooks_analyzed}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-600">Execution Time</p>
                    <p className="font-semibold text-gray-900 mt-1">
                      {report.metadata.agent_completion_time_seconds.toFixed(1)}s
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        ) : null}
      </div>
    </ProtectedRoute>
  );
}
