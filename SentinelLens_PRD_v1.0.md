PRODUCT REQUIREMENTS DOCUMENT
SentinelLens
AI-Powered Microsoft Sentinel Cost Optimization Agent
# 1. Executive Summary
Microsoft Sentinel is a powerful cloud-native SIEM, but most enterprise tenants unknowingly hemorrhage budget by keeping every ingested table in the Analytics (Hot) tier — regardless of whether any active rule, workbook, or hunt query ever touches it. The cost delta between Hot and Archive tier can be 50x per GB.
SentinelLens is an agentic AI tool built on Azure AI Foundry that autonomously audits a Sentinel tenant, maps every analytics rule to the tables it consumes, identifies unused or low-frequency tables, calculates projected savings, and produces a human-approved optimization report with one-click tier migration.
# 2. Goals & Non-Goals
## 2.1  Goals
Autonomously discover all Log Analytics tables in a Sentinel workspace and their current tier configuration.
Parse KQL from every analytics rule, workbook, saved search, and hunt query to build a table usage frequency map.
Calculate actual and projected ingestion cost per table using real Usage data from the workspace.
Produce a structured, human-readable optimization report with savings estimates and migration recommendations.
Require explicit human approval before any tier change is executed — the agent never auto-migrates.
Mask all PII in data flowing through the LLM pipeline using Microsoft Presidio.
Meet OWASP LLM Top 10 requirements through Azure-native security controls.
## 2.2  Non-Goals
SentinelLens does not modify, create, or delete analytics rules.
It does not analyze costs outside of table tier — ingestion pipeline optimization is out of scope for v1.
It does not support non-Azure SIEM platforms (Splunk, Chronicle) in v1.
It does not perform continuous real-time monitoring — it runs as an on-demand audit job.
It does not replace human security review of which tables are mission-critical — it recommends, never decides.
# 3. User Personas
# 4. System Architecture
## 4.1  High-Level Architecture
SentinelLens is composed of four distinct layers: a secure agentic orchestration layer powered by Azure AI Foundry, a FastAPI backend that owns all Azure API interactions, a Next.js frontend for report review and approval, and a dedicated security layer that wraps every data flow.
## 4.2  Agent Orchestration
The agent is built using Azure AI Foundry's Agent SDK (built on OpenAI Assistants API, hosted in Azure). It is given a defined toolset and follows a structured ReAct loop — Reason, Act, Observe — until it has enough data to produce the final report. The LLM used is GPT-4o deployed within the tenant's Azure OpenAI resource, ensuring no data leaves the tenant boundary.
## 4.3  Agentic Tool Set
# 5. Technology Stack
## 5.1  Azure Ecosystem (Primary)
## 5.2  Backend
## 5.3  Frontend
# 6. Security Architecture
## 6.1  OWASP LLM Top 10 Compliance
## 6.2  PII Masking Pipeline
Every data payload flowing from Azure APIs into the LLM context is processed through a two-stage Presidio pipeline before being included in any prompt:
## 6.3  Identity & Access Model
Backend runs with a User-Assigned Managed Identity — no client secrets, no service principal passwords.
Managed Identity is granted Reader on the Sentinel workspace and Log Analytics Reader for query execution.
Write permission (table tier change) is a separate, explicitly scoped role assigned only to the approval service principal.
Frontend users authenticate via Entra ID (MSAL.js). Access to the approval flow requires a dedicated Entra security group.
All secrets (third-party keys, config values) stored in Azure Key Vault. Backend fetches at startup via Managed Identity — no environment variables with secrets.
# 7. Agent Execution Flow
## 7.1  Step-by-Step Flow
## 7.2  Human Approval Gate
Step 11–12 is a hard gate. The agent has no ability to call the tier-change API directly. The approval endpoint is a separate FastAPI route protected by an Entra security group role check. This is not a soft guardrail — it is an architectural separation. The agent thread and the migration executor are entirely different service paths.
# 8. Report Output Specification
## 8.1  Report Sections
Executive Summary: Total tables analyzed, breakdown by usage category, total projected monthly and annual savings.
High Confidence Archive Candidates: Tables with zero rule/workbook/hunt coverage, ingestion volume, current monthly cost, projected savings if moved to Archive.
Low Usage Candidates: Tables referenced in 1–2 rules. Flagged for human review — not auto-recommended.
Active Tables: Tables with 3+ rule references. Explicitly marked as DO NOT TOUCH.
Connector Coverage Map: Which data connectors feed which tables, and whether those tables have downstream rule coverage.
Warnings & Manual Review Items: Complex KQL rules with functions/aliases where table extraction confidence is below threshold, tables that appear unused but are fed by external connectors not in Sentinel.
Execution Metadata: Agent run timestamp, Azure API versions called, confidence scores, KQL parsing success rate.
## 8.2  Savings Calculation Model
# 9. Frontend UX & Key Screens
## 9.1  Screen Map
## 9.2  Key UI Components (ShadCN)
DataTable with column sorting, text filtering, and row selection for the table recommendation lists.
Tabs component to split report into Archive Candidates, Low Usage, Active, and Warnings.
Badge component for tier labels (Hot = red, Basic = amber, Archive = green) and confidence scores.
Sheet (side drawer) for per-table detail drill-down without leaving the report page.
AlertDialog for the approval confirmation — shows final summary of changes before commit.
Progress component + real-time SSE updates for agent execution screen.
Recharts BarChart for savings visualization — grouped by table, color-coded by confidence.
# 10. Backend API Specification
# 11. Infrastructure & Deployment
## 11.1  Azure Resources
## 11.2  Deployment Pipeline
Infrastructure defined as Bicep templates — all resources version-controlled.
GitHub Actions / Azure DevOps pipeline: build → unit tests → container push to ACR → deploy to Container Apps.
Frontend: Next.js build → deploy to Static Web Apps via SWA CLI or GitHub Actions integration.
Environment promotion: dev → staging → prod. Staging environment mirrors prod with a test Sentinel workspace.
# 12. Delivery Milestones
# 13. Risks & Mitigations
# 14. Open Questions
Should v1 support multi-workspace audits (multiple Sentinel workspaces in one report) or single-workspace only?
LAQueryLogs must be explicitly enabled in the tenant to get actual query execution history. Should SentinelLens enable it automatically, or just surface it as a recommendation if it's off?
What is the approval authorization model — individual user approval, or should tier changes require dual approval from two members of a security group?
Should the tool integrate with Azure Cost Management to show actual billed amounts vs our estimates from the Usage table?
For the reporting tier — should reports be stored indefinitely in Blob Storage, or apply a configurable retention policy?

| Version: | 1.0.0 |
|---|---|
| Status: | Draft — For Internal Review |
| Date: | February 2026 |

| The Problem in Numbers |
|---|
| • Average enterprise Sentinel tenant: 60–120 active tables in Hot tier |
| • Typical finding: 30–50% of tables have zero rule coverage |
| • Hot tier cost: ~$0.10–$0.20 / GB / day   |   Archive tier: ~$0.002 / GB / day |
| • Potential savings per mid-size tenant: $3,000 – $15,000 / month |

| Persona | Role | Primary Need | Key Pain Today |
|---|---|---|---|
| Security Architect | Owns SIEM strategy & Sentinel design | Understand true cost footprint of the environment | No visibility into which tables are actually used by rules |
| SOC Manager | Runs day-to-day SOC operations & budget | Reduce monthly Azure bill without breaking detections | Finance pressure but afraid to touch table config manually |
| Cloud Cost Engineer | FinOps / Azure cost optimization | Identify and act on waste across Azure services | Sentinel costs are opaque — cannot audit without security context |
| Sentinel Administrator | Configures data connectors and workspaces | Clean up legacy tables from old connectors | Manual audit of 80+ tables and 200+ rules is impractical |

| Architecture Layers |
|---|
| [Next.js Frontend — ShadCN UI / TanStack Query / Recharts] |
| ↕  REST + SSE (streaming agent progress) |
| [FastAPI Backend — Azure Container Apps] |
| ↕  Azure SDK calls |
| [Azure AI Foundry — Agent + GPT-4o + Tool Functions] |
| ↕  Presidio PII Masking | Prompt Shield |
| [Azure APIs — Sentinel API / Log Analytics API / Monitor API] |

| Tool Name | What It Does | API / SDK Used |
|---|---|---|
| list_workspace_tables | Fetches all tables with tier, retention, schema | azure-mgmt-loganalytics |
| get_ingestion_volume | Queries Usage table for GB/day per table (last 30d) | azure-monitor-query (KQL) |
| list_analytics_rules | Fetches all Scheduled/NRT rules with raw KQL | azure-mgmt-securityinsight |
| list_workbooks | Fetches workbook JSON blobs, extracts KQL datasources | azure-mgmt-securityinsight |
| list_hunt_queries | Fetches saved hunt queries and their KQL | azure-mgmt-securityinsight |
| parse_kql_tables | Extracts table names from KQL strings (regex + parser) | Internal — python-kql + regex |
| list_data_connectors | Lists all active data connectors and their table mappings | azure-mgmt-securityinsight |
| calculate_savings | Computes cost delta (Hot vs Archive) per candidate table | Internal — Azure pricing constants |
| generate_report | Assembles structured JSON report with recommendations | Internal — Pydantic schema |

| Component | Azure Service | Why |
|---|---|---|
| LLM | Azure OpenAI — GPT-4o (via AI Foundry) | Data stays in tenant. Best-in-class tool calling. Foundry manages deployments. |
| Agent Orchestration | Azure AI Foundry Agent SDK | Native tool-calling loop, thread management, streaming. No need for LangChain. |
| Backend Hosting | Azure Container Apps | Serverless containers, auto-scale to zero, built-in HTTPS ingress. |
| Frontend Hosting | Azure Static Web Apps | Free tier available. Integrated CI/CD from GitHub Actions. |
| Authentication | Azure Managed Identity + Entra ID | Zero stored secrets. RBAC-gated access to all Azure APIs. |
| Secrets | Azure Key Vault | All third-party credentials and config stored here. Never in code. |
| PII Masking | Microsoft Presidio (open source) | Strips IPs, emails, usernames before data hits LLM. Azure-deployable. |
| Prompt Security | Azure AI Content Safety + Prompt Shield | OWASP LLM01 (Prompt Injection) mitigation. GA service, one API call. |
| Audit Logging | Azure Monitor / Log Analytics | All agent actions and API calls logged to a dedicated audit workspace. |
| Container Registry | Azure Container Registry | Stores Docker images for backend. Integrated vulnerability scanning. |
| CI/CD | Azure DevOps Pipelines / GitHub Actions | Build, test, push, deploy pipeline. Bicep for infra-as-code. |

| Library / Framework | Purpose |
|---|---|
| FastAPI (Python) | REST API framework. Async-first. OpenAPI docs auto-generated. |
| azure-mgmt-securityinsight | Sentinel analytics rules, connectors, workbooks API |
| azure-mgmt-loganalytics | Table listing, tier management |
| azure-monitor-query | Run KQL queries (Usage table, LAQueryLogs) |
| azure-identity | ManagedIdentityCredential — no stored secrets anywhere |
| presidio-analyzer + presidio-anonymizer | PII detection and masking pipeline |
| pydantic v2 | All API request/response schemas. Enforces structured LLM output. |
| python-kql (+ regex fallback) | KQL AST parsing to extract table names from rule queries |
| pytest + pytest-asyncio | Unit and integration testing |

| Library / Framework | Purpose |
|---|---|
| Next.js 14 (App Router) | React framework. SSR for report pages, client-side for interactive dashboard. |
| ShadCN UI | Component library. Clean, accessible, fully customizable. No vendor lock-in. |
| Tailwind CSS | Utility-first styling. Pairs perfectly with ShadCN. |
| TanStack Query (React Query) | Server state management. Handles polling for agent job status. |
| Recharts | Cost visualization — bar charts (savings by table), line charts (trend over time). |
| Zustand | Client-side state for report review flow and approval selections. |
| MSAL.js (Azure AD Auth) | Entra ID authentication in the browser. Token-based API calls. |
| TypeScript | End-to-end type safety. API types generated from FastAPI OpenAPI spec. |

| OWASP LLM Risk | Mitigation in SentinelLens |
|---|---|
| LLM01 — Prompt Injection | Azure Prompt Shield runs on every user input and on all data ingested from APIs before it touches the LLM prompt. |
| LLM02 — Insecure Output Handling | All LLM outputs are parsed against a strict Pydantic schema. Raw LLM text is never executed or directly rendered. |
| LLM03 — Training Data Poisoning | N/A — uses Azure OpenAI hosted model, not a fine-tuned model. |
| LLM04 — Model Denial of Service | Azure OpenAI throttling + token budget per agent run enforced server-side. |
| LLM05 — Supply Chain | All dependencies pinned. Azure Container Registry scans images. SBOM generated on every build. |
| LLM06 — Sensitive Info Disclosure | Microsoft Presidio masks PII (IPs, emails, UPNs, hostnames) before any data enters the LLM context window. |
| LLM07 — Insecure Plugin Design | Agent tools are read-only by design. Write operations (tier change) are in a separate, human-gated API path. |
| LLM08 — Excessive Agency | Agent cannot execute tier changes. A separate human approval endpoint with Entra ID auth gates all mutations. |
| LLM09 — Overreliance | Every recommendation includes a confidence score and an explicit 'verify before acting' disclaimer in the report. |
| LLM10 — Model Theft | Models are hosted in Azure OpenAI within the tenant. No external API calls. |

| PII Masking Flow |
|---|
| Raw API Data (rule KQL, table names, connector metadata) |
| ↓ |
| Stage 1 — presidio-analyzer: Detects IP_ADDRESS, EMAIL_ADDRESS, PERSON, DOMAIN_NAME, URL, PHONE_NUMBER |
| ↓ |
| Stage 2 — presidio-anonymizer: Replaces detected entities with typed placeholders e.g. <IP_ADDRESS_1> |
| ↓ |
| Sanitized payload enters LLM prompt — no raw PII ever reaches the model |
| ↓ |
| LLM output passed back — placeholders preserved in report output |

| Step | Actor | Action | Output |
|---|---|---|---|
| 1 | User | Initiates audit job via frontend — selects workspace, date range | Job ID created, status: QUEUED |
| 2 | FastAPI | Validates Entra token, creates agent thread in AI Foundry, starts async job | Thread ID, status: RUNNING |
| 3 | Agent | Calls list_workspace_tables tool | Table list with tier + retention |
| 4 | Agent | Calls get_ingestion_volume tool — queries Usage table via KQL | GB/day per table, last 30 days |
| 5 | Agent | Calls list_analytics_rules, list_workbooks, list_hunt_queries | All KQL strings collected |
| 6 | Agent | Calls parse_kql_tables on each KQL string — extracts table references | Usage frequency map per table |
| 7 | Agent | Calls list_data_connectors — maps connectors to tables | Connector ↔ table mapping |
| 8 | Agent | Calls calculate_savings — computes Hot vs Archive delta per candidate | Savings estimate per table + total |
| 9 | Agent | Calls generate_report — assembles Pydantic-validated JSON report | Structured report object |
| 10 | FastAPI | Stores report in Azure Blob Storage, updates job status: AWAITING_APPROVAL | Report URL returned to frontend |
| 11 | User | Reviews report in frontend dashboard, selects tables to migrate | Approval payload |
| 12 | FastAPI | Validates approval, calls Log Analytics Tables API to update tier | Tier change confirmed, audit log written |

| Cost Formula |
|---|
| hot_daily_cost      = ingestion_gb_per_day × $0.10  (Analytics tier, approximate) |
| archive_daily_cost  = ingestion_gb_per_day × $0.002 (Archive tier, approximate) |
| monthly_savings     = (hot_daily_cost − archive_daily_cost) × 30 |
| annual_savings      = monthly_savings × 12 |
|  |
| Note: Prices fetched from Azure Retail Prices API at report generation time for accuracy. |
| Actual prices vary by region and negotiated enterprise agreements. |

| Screen | Route | Description |
|---|---|---|
| Dashboard | /dashboard | Overview of all past and current audit jobs. Status badges. Quick savings summary from last run. |
| New Audit | /audit/new | Workspace selector (pulls from Entra-accessible subscriptions). Date range. One-click start. |
| Audit Progress | /audit/[jobId]/progress | Live SSE streaming of agent step completions. Shows current tool being called. Progress bar. |
| Report View | /audit/[jobId]/report | Full report. Tables categorized into tabs: Archive Candidates / Low Usage / Active / Warnings. Savings bar chart via Recharts. Per-table details in ShadCN DataTable with sort/filter. |
| Approval Flow | /audit/[jobId]/approve | Checkboxes on archive candidates. Savings recalculates live as user selects/deselects. Confirm button triggers migration with Entra auth challenge. |
| History | /history | All past reports. Filter by workspace, date range. Download report as JSON or PDF. |

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | /api/v1/workspaces | List accessible Sentinel workspaces for the authenticated user | Entra ID Token |
| POST | /api/v1/audits | Start a new audit job. Body: { workspace_id, subscription_id, days_lookback } | Entra ID Token |
| GET | /api/v1/audits/{job_id} | Get audit job status and metadata | Entra ID Token |
| GET | /api/v1/audits/{job_id}/stream | SSE stream of agent progress events | Entra ID Token |
| GET | /api/v1/audits/{job_id}/report | Get the full structured report JSON | Entra ID Token |
| POST | /api/v1/audits/{job_id}/approve | Submit approval payload to execute tier changes. Body: { table_names: [] } | Entra ID Token + Security Group |
| GET | /api/v1/audits | List all audit jobs with pagination | Entra ID Token |
| GET | /api/v1/health | Health check endpoint | None |

| Resource | SKU / Tier | Purpose |
|---|---|---|
| Azure Container Apps | Consumption plan | Backend FastAPI — scales to zero when idle |
| Azure Static Web Apps | Free / Standard | Next.js frontend |
| Azure OpenAI | GPT-4o (AI Foundry deployment) | LLM for agent reasoning |
| Azure AI Foundry Project | Standard | Agent threads, tool config, observability |
| Azure Container Registry | Basic | Docker images for backend |
| Azure Key Vault | Standard | Secrets and configuration |
| Azure Blob Storage | LRS, Hot | Report JSON storage |
| Log Analytics Workspace (Audit) | Pay-per-GB | Audit logs for all agent actions |
| Azure Monitor | Standard | Metrics, alerts, dashboards |
| Managed Identity (User-Assigned) | N/A | Auth for all Azure API calls from backend |

| Phase | Duration | Deliverables |
|---|---|---|
| Phase 1 — Foundation | Week 1–2 | Azure infra provisioned via Bicep. Managed Identity + RBAC configured. FastAPI skeleton with health endpoint. Azure SDK integrations: tables, rules, connectors, usage query all returning real data. |
| Phase 2 — Agent Core | Week 3–4 | All 9 agent tools implemented and tested. KQL parser with regex fallback. AI Foundry agent configured with tools. Agent loop running end-to-end in dev workspace. Pydantic report schema finalized. |
| Phase 3 — Security Layer | Week 5 | Presidio PII masking pipeline integrated. Prompt Shield on all inputs. OWASP review completed. Key Vault for all secrets. Audit logging to Log Analytics. |
| Phase 4 — Frontend | Week 6–7 | Next.js + ShadCN setup. All 6 screens implemented. SSE streaming progress. Recharts savings visualizations. Entra ID auth with MSAL.js. Approval flow with security group gate. |
| Phase 5 — Hardening & Release | Week 8 | End-to-end testing on 2+ real tenants. KQL parser edge case handling. Performance tuning. Documentation. Staging → prod promotion. |

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| KQL parser misses tables in complex rules (functions, aliases, dynamic union) | High | Medium | Confidence scoring per rule. Complex rules flagged for manual review. Never auto-recommend based on low-confidence parse. |
| Tables used by external systems not visible in Sentinel rules (e.g. Power BI, external SIEM) | Medium | High | Report includes explicit 'external dependency' warning section. LAQueryLogs analysis (if enabled) cross-checks actual query history. |
| Azure pricing changes invalidate savings calculations | Low | Low | Savings calculated using Azure Retail Prices API at report generation time, not hardcoded constants. |
| Agent token context window exhausted in large tenants (200+ rules) | Medium | Medium | Tool calls are batched and summarized before entering LLM context. Raw KQL not passed to LLM — only parsed table names. |
| Managed Identity lacks permissions in customer tenant | Medium | High | Pre-flight permission check endpoint validates all required RBAC roles before starting audit job. Clear error messages with required role names. |