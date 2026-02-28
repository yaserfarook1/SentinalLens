/**
 * TypeScript Type Definitions for SentinelLens Frontend
 *
 * Defines all interfaces for API responses, component props, and data models.
 * Ensures type safety across the frontend.
 */

/**
 * User Information from Entra ID
 */
export interface User {
  id: string;
  displayName: string;
  email: string;
  principalName: string;
}

/**
 * Azure Workspace Information
 */
export interface WorkspaceInfo {
  workspace_id: string;
  workspace_name: string;
  subscription_id: string;
  resource_group: string;
  location?: string;
}

/**
 * Audit Job Information
 */
export interface AuditJob {
  job_id: string;
  workspace_id: string;
  workspace_name: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  status: "pending" | "running" | "completed" | "failed" | "Completed" | "Running" | "Queued" | "Failed";
  progress_percentage: number;
  current_step?: string;
  total_steps?: number;
  error_message?: string;
  tables_analyzed?: number;
  total_savings?: number;
  archive_candidates_count?: number;
}

/**
 * Table Recommendation from Analysis
 */
export interface TableRecommendation {
  table_name: string;
  table_id: string;
  current_tier: string;
  recommended_tier: string;
  confidence: "HIGH" | "MEDIUM" | "LOW";
  reason: string;
  ingestion_volume_gb_per_day?: number;
  ingestion_gb_per_day: number; // Primary field
  monthly_savings: number;
  annual_savings: number;
  rule_coverage_count: number;
  workbook_coverage_count: number;
  hunt_query_coverage_count: number;
  data_connector_count: number;
}

/**
 * Warning in Report
 */
export interface Warning {
  warning_type: string;
  table_name?: string;
  description: string;
  recommendation: string;
}

/**
 * Report Metadata
 */
export interface ReportMetadata {
  [key: string]: any;
}

/**
 * Audit Report Summary
 */
export interface AuditReport {
  job_id: string;
  workspace_id: string;
  workspace_name: string;
  audit_date: string;
  days_lookback: number;
  total_tables: number;
  total_ingestion_gb_per_day: number;
  archive_candidates: TableRecommendation[];
  low_usage_tables: TableRecommendation[];
  active_tables: TableRecommendation[];
  total_monthly_savings: number;
  total_annual_savings: number;
  kql_parser_accuracy_percentage: number;
  warnings?: (string | Warning)[];
  errors?: string[];
  metadata?: ReportMetadata;
}

/**
 * Progress Update (from SSE stream)
 */
export interface ProgressUpdate {
  job_id: string;
  status: "running" | "completed" | "failed";
  progress_percentage: number;
  current_step: string;
  total_steps: number;
  message: string;
  timestamp: string;
  error?: string;
}

/**
 * Approval Request
 */
export interface ApprovalRequest {
  job_id: string;
  tables_to_migrate: string[];
  target_tier: string;
}

/**
 * Approval Response
 */
export interface ApprovalResponse {
  status: "success" | "failed";
  message: string;
  migration_id?: string;
  approved_table_count?: number;
  migrated_tables?: string[];
  errors?: { table_name: string; error: string }[];
}

/**
 * API Response Wrapper
 */
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

/**
 * Paginated Response
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/**
 * Audit History Item
 */
export interface AuditHistoryItem {
  job_id: string;
  workspace_id: string;
  workspace_name: string;
  created_at: string;
  completed_at?: string;
  status: "pending" | "running" | "completed" | "failed";
  tables_analyzed: number;
  archive_candidates_count: number;
  total_monthly_savings: number;
}

/**
 * Dashboard Summary
 */
export interface DashboardSummary {
  total_audits: number;
  completed_audits: number;
  running_audits: number;
  total_monthly_savings: number;
  total_annual_savings: number;
  archive_candidates_total: number;
  average_tables_analyzed: number;
  success_rate_percentage: number;
}

/**
 * Error Response
 */
export interface ErrorResponse {
  detail: string;
  status: number;
  timestamp?: string;
  path?: string;
}

/**
 * Setup Credentials Request
 */
export interface SetupCredentialsRequest {
  client_id: string;
  client_secret: string;
}

/**
 * Setup Credentials Response
 */
export interface SetupCredentialsResponse {
  status: string;
  message: string;
  env_file: string;
}

/**
 * Report Interface (alias for AuditReport)
 */
export type Report = AuditReport;

/**
 * Audit Progress Update (alias for ProgressUpdate)
 */
export type AuditProgress = ProgressUpdate;

/**
 * Workspace Info (alias for WorkspaceInfo)
 */
export type Workspace = WorkspaceInfo;
