"""
Azure AI Foundry Agent Orchestrator

Manages agent lifecycle, tool execution, and result collection.
Implements ReAct loop: Reason → Act → Observe
"""

import logging
import asyncio
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from src.config import settings
from src.models.schemas import (
    AnalyticsRule, Workbook, HuntQuery, DataConnector, TableIngestionData,
    KqlParseResult, Report
)
from src.services.azure_api import azure_api_service
from src.services.kql_parser import kql_parser
from src.services.cost_calculator import cost_calculator
from src.services.report_generator import report_generator
from src.security import pii_masking, prompt_shield, data_sanitizer
from src.security_middleware import security_middleware
from src.utils.logging import AuditLogger

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates the SentinelLens agent workflow.

    ReAct Loop Flow:
    1. Reason: Understand the audit goal
    2. Act: Execute tools to gather data
    3. Observe: Collect results and process
    4. Repeat until sufficient data to generate report
    """

    def __init__(self):
        """Initialize agent orchestrator"""
        self.agent_id = None
        self.execution_start_time = None
        self.execution_times = {}
        self.tokens_used = 0
        self.max_tokens = settings.AGENT_MAX_TOKENS_PER_RUN
        self.tool_results = {}

        logger.info("[AGENT] Orchestrator initialized")

    async def execute_audit(
        self,
        job_id: str,
        workspace_id: str,
        subscription_id: str,
        resource_group: str,
        workspace_name: str,
        days_lookback: int = 30
    ) -> Report:
        """
        Execute complete audit workflow.

        Args:
            job_id: Unique audit job ID
            workspace_id: Sentinel workspace ID
            subscription_id: Azure subscription ID
            resource_group: Resource group name
            workspace_name: Workspace display name
            days_lookback: Days of history to analyze

        Returns:
            Completed Report object

        Raises:
            Exception: If audit fails
        """
        self.agent_id = job_id
        self.execution_start_time = time.time()

        try:
            logger.info(f"[AGENT] Starting audit execution: job_id={job_id}")

            # ===== STEP 1: List all tables =====
            logger.info("[AGENT] STEP 1: Fetching workspace tables")
            tables = await self._execute_tool(
                "list_workspace_tables",
                lambda: azure_api_service.list_workspace_tables(resource_group, workspace_name)
            )

            if not tables:
                raise Exception("No tables found in workspace")

            logger.info(f"[AGENT] Found {len(tables)} tables")

            # ===== STEP 2: Get ingestion volume =====
            logger.info("[AGENT] STEP 2: Fetching ingestion volume data")
            ingestion_data = await self._execute_tool(
                "get_ingestion_volume",
                lambda: azure_api_service.get_ingestion_volume(
                    resource_group, workspace_name, days_lookback
                )
            )

            logger.info(f"[AGENT] Ingestion data retrieved for {len(ingestion_data)} tables")

            # ===== STEP 3: List analytics rules =====
            logger.info("[AGENT] STEP 3: Fetching analytics rules")
            rules = await self._execute_tool(
                "list_analytics_rules",
                lambda: azure_api_service.list_analytics_rules(resource_group, workspace_name)
            )

            logger.info(f"[AGENT] Found {len(rules)} analytics rules")

            # ===== SECURITY: Validate and mask KQL queries =====
            logger.info("[AGENT] Applying security controls: validating and masking KQL")
            rules = security_middleware.validate_and_mask_kql_queries(rules)
            security_middleware.log_security_event(
                event_type="KQL_VALIDATION_COMPLETE",
                severity="LOW",
                details=f"Validated {len(rules)} KQL queries"
            )

            # ===== STEP 4: Parse KQL from rules =====
            logger.info("[AGENT] STEP 4: Parsing KQL queries")
            kql_queries = [rule.kql_query for rule in rules if rule.kql_query]

            kql_parse_results = await self._execute_tool(
                "parse_kql_tables",
                lambda: kql_parser.batch_parse(kql_queries)
            )

            # Map parsed tables back to rules
            for rule, parse_result in zip(rules, kql_parse_results):
                rule.tables_referenced = parse_result.tables
                rule.parsing_confidence = parse_result.parsing_confidence

            parse_success_rate = sum(1 for r in kql_parse_results if r.success) / len(kql_parse_results) if kql_parse_results else 0
            logger.info(f"[AGENT] KQL parsing complete: {parse_success_rate:.1%} success rate")

            # ===== STEP 5: List workbooks =====
            logger.info("[AGENT] STEP 5: Fetching workbooks")
            workbooks = await self._execute_tool(
                "list_workbooks",
                lambda: azure_api_service.list_workbooks(resource_group, workspace_name)
            )

            logger.info(f"[AGENT] Found {len(workbooks)} workbooks")

            # ===== STEP 6: List hunt queries =====
            logger.info("[AGENT] STEP 6: Fetching hunt queries")
            hunt_queries = await self._execute_tool(
                "list_hunt_queries",
                lambda: azure_api_service.list_hunt_queries(resource_group, workspace_name)
            )

            logger.info(f"[AGENT] Found {len(hunt_queries)} hunt queries")

            # ===== STEP 7: List data connectors =====
            logger.info("[AGENT] STEP 7: Fetching data connectors")
            connectors = await self._execute_tool(
                "list_data_connectors",
                lambda: azure_api_service.list_data_connectors(resource_group, workspace_name)
            )

            logger.info(f"[AGENT] Found {len(connectors)} data connectors")

            # ===== SECURITY: Mask connector metadata =====
            logger.info("[AGENT] Applying security controls: masking connector metadata")
            connectors = security_middleware.mask_connector_metadata(connectors)
            security_middleware.log_security_event(
                event_type="CONNECTOR_METADATA_MASKED",
                severity="LOW",
                details=f"Masked metadata for {len(connectors)} connectors"
            )

            # ===== STEP 8: Calculate savings =====
            logger.info("[AGENT] STEP 8: Calculating cost savings")
            tables_with_costs = []

            for table in tables:
                ingestion_gb = ingestion_data.get(table.table_name, 0.0)
                costs = cost_calculator.calculate_table_costs(ingestion_gb, table.current_tier, "Archive")

                table_data = {
                    "table_name": table.table_name,
                    "ingestion_gb_day": ingestion_gb,
                    "costs": costs
                }
                tables_with_costs.append(table_data)

            logger.info("[AGENT] Cost calculations complete")

            # ===== STEP 9: Generate report =====
            logger.info("[AGENT] STEP 9: Generating optimization report")

            execution_time = time.time() - self.execution_start_time

            report = await self._execute_tool(
                "generate_report",
                lambda: report_generator.generate_report(
                    job_id=job_id,
                    workspace_id=workspace_id,
                    workspace_name=workspace_name,
                    tables=tables,
                    rules=rules,
                    ingestion_data=ingestion_data,
                    connectors=connectors,
                    kql_parse_results=kql_parse_results,
                    agent_tokens_used=self.tokens_used,
                    agent_max_tokens=self.max_tokens,
                    agent_run_seconds=execution_time
                )
            )

            logger.info(
                f"[AGENT] Audit execution complete: "
                f"job_id={job_id} "
                f"tables={len(tables)} "
                f"annual_savings=${report.summary.total_annual_savings:,.0f} "
                f"execution_time={execution_time:.1f}s"
            )

            # ===== SECURITY: Audit logging for completed audit =====
            logger.info("[AGENT] Logging audit completion event")
            security_middleware.log_security_event(
                event_type="AUDIT_COMPLETED",
                severity="LOW",
                details=f"Audit completed: {len(tables)} tables, ${report.summary.total_annual_savings:,.0f} savings identified"
            )

            return report

        except asyncio.TimeoutError:
            logger.error(f"[AGENT] Execution timeout after {settings.AGENT_TIMEOUT_SECONDS}s")
            raise

        except Exception as e:
            logger.error(f"[AGENT] Execution failed: {str(e)}")
            raise

    async def _execute_tool(self, tool_name: str, tool_func) -> any:
        """
        Execute a single tool with monitoring.

        Tracks execution time, token usage, and logs tool calls.

        Args:
            tool_name: Name of tool (for logging)
            tool_func: Async callable that executes the tool

        Returns:
            Tool result

        Raises:
            Exception: If tool execution fails or times out
        """
        start_time = time.time()

        try:
            logger.info(f"[AGENT] Executing tool: {tool_name}")

            # Execute tool with timeout
            result = await asyncio.wait_for(
                asyncio.to_thread(tool_func),
                timeout=settings.AGENT_TIMEOUT_SECONDS
            )

            execution_time = time.time() - start_time
            self.execution_times[tool_name] = execution_time

            # Log tool completion
            result_count = len(result) if isinstance(result, (list, dict)) else 1
            logger.info(
                f"[AGENT] Tool complete: {tool_name} "
                f"(results: {result_count}, time: {execution_time:.2f}s)"
            )

            return result

        except asyncio.TimeoutError:
            logger.error(f"[AGENT] Tool timeout: {tool_name}")
            raise

        except Exception as e:
            logger.error(f"[AGENT] Tool failed: {tool_name} - {str(e)}")
            raise

    def check_token_budget(self):
        """Check if agent has exceeded token budget"""
        if self.tokens_used >= self.max_tokens:
            raise Exception(f"Token budget exceeded: {self.tokens_used} >= {self.max_tokens}")

    def get_execution_summary(self) -> Dict:
        """Get summary of agent execution"""
        if not self.execution_start_time:
            return {}

        total_time = time.time() - self.execution_start_time

        return {
            "agent_id": self.agent_id,
            "total_execution_time": total_time,
            "tool_execution_times": self.execution_times,
            "tokens_used": self.tokens_used,
            "tokens_limit": self.max_tokens
        }


# ===== SINGLETON INSTANCE =====
agent_orchestrator = AgentOrchestrator()
