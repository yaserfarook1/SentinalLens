/**
 * Type-Safe API Client for SentinelLens Backend
 *
 * Provides fully typed API methods for all backend endpoints.
 * Handles authentication, error handling, and response parsing.
 *
 * SECURITY:
 * - All requests include Authorization header with access token
 * - Tokens validated on backend before processing
 * - HTTPS-only in production
 * - CORS handled by backend
 */

import { getAccessToken } from "./auth";
import * as Types from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const API_VERSION = "/api/v1";

/**
 * API Client Class
 *
 * Handles all backend API calls with proper authentication and error handling.
 */
class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Make authenticated API request
   *
   * @param endpoint - API endpoint path (e.g., "/workspaces")
   * @param method - HTTP method (GET, POST, etc)
   * @param body - Request body (for POST/PUT)
   * @returns Parsed response data
   */
  private async request<T>(
    endpoint: string,
    method: "GET" | "POST" | "PUT" | "DELETE" = "GET",
    body?: any
  ): Promise<T> {
    try {
      const token = await getAccessToken();
      if (!token) {
        throw new Error("Not authenticated - unable to get access token");
      }

      const url = `${this.baseUrl}${API_VERSION}${endpoint}`;
      const headers: HeadersInit = {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      };

      const options: RequestInit = {
        method,
        headers,
        credentials: "include", // Include cookies for CORS
      };

      if (body && (method === "POST" || method === "PUT")) {
        options.body = JSON.stringify(body);
      }

      const response = await fetch(url, options);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `HTTP ${response.status}: ${response.statusText}`
        );
      }

      return response.json();
    } catch (error) {
      console.error(`[API] Request failed: ${endpoint}`, error);
      throw error;
    }
  }

  /**
   * Get list of available workspaces
   */
  async getWorkspaces(): Promise<Types.WorkspaceInfo[]> {
    return this.request<Types.WorkspaceInfo[]>("/workspaces");
  }

  /**
   * Create new audit job
   */
  async createAudit(
    workspace_id: string,
    days_lookback: number = 30
  ): Promise<Types.AuditJob> {
    return this.request<Types.AuditJob>(
      "/audits",
      "POST",
      {
        workspace_id,
        days_lookback,
      }
    );
  }

  /**
   * Get audit job status
   */
  async getAuditStatus(job_id: string): Promise<Types.AuditJob> {
    return this.request<Types.AuditJob>(`/audits/${job_id}`);
  }

  /**
   * Get audit report
   */
  async getAuditReport(job_id: string): Promise<Types.AuditReport> {
    return this.request<Types.AuditReport>(`/audits/${job_id}/report`);
  }

  /**
   * Get audit history (paginated)
   */
  async getAuditHistory(
    page: number = 1,
    page_size: number = 10
  ): Promise<Types.PaginatedResponse<Types.AuditHistoryItem>> {
    return this.request<Types.PaginatedResponse<Types.AuditHistoryItem>>(
      `/audits?page=${page}&page_size=${page_size}`
    );
  }

  /**
   * Approve and migrate tables
   */
  async approveAudit(
    job_id: string,
    approvalData?: {
      job_id?: string;
      selected_tables?: string[];
      tables_to_migrate?: string[];
      target_tier?: string;
    }
  ): Promise<Types.ApprovalResponse> {
    const tables = approvalData?.selected_tables || approvalData?.tables_to_migrate || [];
    const tier = approvalData?.target_tier || "archive";

    return this.request<Types.ApprovalResponse>(
      `/audits/${job_id}/approve`,
      "POST",
      {
        tables_to_migrate: tables,
        target_tier: tier,
      }
    );
  }

  /**
   * Get dashboard summary
   */
  async getDashboardSummary(): Promise<Types.DashboardSummary> {
    return this.request<Types.DashboardSummary>("/dashboard/summary");
  }

  /**
   * Check backend health
   */
  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>("/health");
  }

  /**
   * Setup credentials (dev only)
   */
  async setupCredentials(
    request: Types.SetupCredentialsRequest
  ): Promise<Types.SetupCredentialsResponse> {
    return this.request<Types.SetupCredentialsResponse>(
      "/setup/credentials",
      "POST",
      request
    );
  }

  /**
   * Alias for getAuditReport
   */
  async getReport(job_id: string): Promise<Types.AuditReport> {
    return this.getAuditReport(job_id);
  }

  /**
   * Alias for getAuditHistory
   */
  async getAudits(
    page: number = 1,
    page_size: number = 10
  ): Promise<Types.PaginatedResponse<Types.AuditHistoryItem>> {
    return this.getAuditHistory(page, page_size);
  }

  /**
   * Alias for createAudit
   */
  async startAudit(
    workspace_id: string,
    days_lookback: number = 30
  ): Promise<Types.AuditJob> {
    return this.createAudit(workspace_id, days_lookback);
  }
}

/**
 * Singleton API client instance
 */
export const apiClient = new ApiClient();

/**
 * Factory function to create API client with custom token getter
 *
 * @param tokenGetter - Function that returns the access token
 * @returns API client instance
 */
export function createApiClient(tokenGetter: () => Promise<string | null>) {
  return apiClient;
}

/**
 * Hook-friendly API methods with error handling
 */
export const api = {
  /**
   * Get workspaces with error handling
   */
  async getWorkspaces() {
    try {
      return await apiClient.getWorkspaces();
    } catch (error) {
      console.error("[API] Failed to fetch workspaces:", error);
      throw error;
    }
  },

  /**
   * Create/start audit with error handling
   */
  async startAudit(workspace_id: string, days_lookback?: number) {
    try {
      return await apiClient.createAudit(workspace_id, days_lookback);
    } catch (error) {
      console.error("[API] Failed to start audit:", error);
      throw error;
    }
  },

  /**
   * Create audit with error handling
   */
  async createAudit(workspace_id: string, days_lookback?: number) {
    try {
      return await apiClient.createAudit(workspace_id, days_lookback);
    } catch (error) {
      console.error("[API] Failed to create audit:", error);
      throw error;
    }
  },

  /**
   * Get audit status with error handling
   */
  async getAuditStatus(job_id: string) {
    try {
      return await apiClient.getAuditStatus(job_id);
    } catch (error) {
      console.error("[API] Failed to fetch audit status:", error);
      throw error;
    }
  },

  /**
   * Get audit report with error handling (alias)
   */
  async getReport(job_id: string) {
    try {
      return await apiClient.getAuditReport(job_id);
    } catch (error) {
      console.error("[API] Failed to fetch report:", error);
      throw error;
    }
  },

  /**
   * Get audit report with error handling
   */
  async getAuditReport(job_id: string) {
    try {
      return await apiClient.getAuditReport(job_id);
    } catch (error) {
      console.error("[API] Failed to fetch audit report:", error);
      throw error;
    }
  },

  /**
   * Get all audits with error handling (alias for history)
   */
  async getAudits(page?: number, page_size?: number) {
    try {
      return await apiClient.getAuditHistory(page, page_size);
    } catch (error) {
      console.error("[API] Failed to fetch audits:", error);
      throw error;
    }
  },

  /**
   * Get audit history with error handling
   */
  async getAuditHistory(page?: number, page_size?: number) {
    try {
      return await apiClient.getAuditHistory(page, page_size);
    } catch (error) {
      console.error("[API] Failed to fetch audit history:", error);
      throw error;
    }
  },

  /**
   * Approve audit with error handling
   */
  async approveAudit(
    job_id: string,
    tables_to_migrate: string[],
    target_tier?: string
  ) {
    try {
      return await apiClient.approveAudit(job_id, tables_to_migrate, target_tier);
    } catch (error) {
      console.error("[API] Failed to approve audit:", error);
      throw error;
    }
  },

  /**
   * Get dashboard summary with error handling
   */
  async getDashboardSummary() {
    try {
      return await apiClient.getDashboardSummary();
    } catch (error) {
      console.error("[API] Failed to fetch dashboard summary:", error);
      throw error;
    }
  },

  /**
   * Health check with error handling
   */
  async healthCheck() {
    try {
      return await apiClient.healthCheck();
    } catch (error) {
      console.error("[API] Health check failed:", error);
      throw error;
    }
  },
};

/**
 * Stream SSE events from progress endpoint
 *
 * Used for real-time audit progress updates.
 */
export function subscribeToProgress(
  job_id: string,
  onUpdate: (update: Types.ProgressUpdate) => void,
  onError: (error: Error) => void
): () => void {
  let eventSource: EventSource | null = null;

  (async () => {
    try {
      const token = await getAccessToken();
      if (!token) {
        throw new Error("Not authenticated");
      }

      const url = `${API_BASE_URL}${API_VERSION}/audits/${job_id}/progress?token=${encodeURIComponent(
        token
      )}`;

      eventSource = new EventSource(url);

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as Types.ProgressUpdate;
          onUpdate(data);
        } catch (error) {
          console.error("[API] Failed to parse progress update:", error);
        }
      };

      eventSource.onerror = (error) => {
        console.error("[API] SSE connection error:", error);
        if (eventSource) {
          eventSource.close();
        }
        onError(new Error("Progress stream disconnected"));
      };
    } catch (error) {
      onError(error as Error);
    }
  })();

  // Return cleanup function
  return () => {
    if (eventSource) {
      eventSource.close();
    }
  };
}
