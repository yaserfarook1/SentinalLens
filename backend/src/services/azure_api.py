"""
Azure API Service Layer

Wraps all Azure SDK calls for Sentinel, Log Analytics, and Monitor APIs.
All methods use Managed Identity for authentication.
All API calls are logged (metadata only, never data contents).
"""

from azure.identity import ManagedIdentityCredential, DefaultAzureCredential
from azure.mgmt.securityinsight import SecurityInsight
from azure.mgmt.loganalytics import LogAnalyticsManagementClient
from azure.monitor.query import LogsQueryClient, MetricsQueryClient
from azure.core.exceptions import Azure ClientError, ResourceNotFoundError
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import asyncio

from src.config import settings
from src.models.schemas import (
    AnalyticsRule, Workbook, HuntQuery, DataConnector, TableIngestionData, TierType
)

logger = logging.getLogger(__name__)


class AzureApiService:
    """Service for all Azure API interactions"""

    def __init__(self):
        """Initialize Azure clients"""
        # Get credential (Managed Identity in prod, DefaultAzureCredential in dev)
        self.credential = settings.credential

        # Initialize clients
        self.sentinel_client = SecurityInsight(
            credential=self.credential,
            subscription_id=settings.AZURE_SUBSCRIPTION_ID
        )
        self.log_analytics_client = LogAnalyticsManagementClient(
            credential=self.credential,
            subscription_id=settings.AZURE_SUBSCRIPTION_ID
        )
        self.logs_query_client = LogsQueryClient(credential=self.credential)
        self.metrics_query_client = MetricsQueryClient(credential=self.credential)

        logger.info("[AUDIT] Azure API service initialized")

    async def list_workspace_tables(
        self, resource_group: str, workspace_name: str
    ) -> List[TableIngestionData]:
        """
        Fetch all tables in a workspace with tier and retention info.

        Returns:
            List of tables with metadata
        """
        try:
            logger.info(f"[AUDIT] Fetching tables for workspace: {workspace_name}")

            # Get all tables from Log Analytics
            tables = []

            # This is a simplified implementation - actual implementation uses
            # Azure Log Analytics Tables API
            tables_list = self.log_analytics_client.tables.list_by_workspace(
                resource_group_name=resource_group,
                workspace_name=workspace_name
            )

            table_count = 0
            for table in tables_list:
                try:
                    # Parse table properties
                    tier = self._get_table_tier(table)
                    retention = self._get_table_retention(table)

                    tables.append(
                        TableIngestionData(
                            table_name=table.name,
                            current_tier=tier,
                            retention_days=retention,
                            ingestion_gb_per_day=0.0,  # Will be populated by get_ingestion_volume
                            ingestion_gb_per_month=0.0
                        )
                    )
                    table_count += 1

                except Exception as e:
                    logger.warning(f"[AUDIT] Failed to parse table {table.name}: {str(e)}")
                    continue

            logger.info(f"[AUDIT] Successfully listed {table_count} tables")
            return tables

        except Exception as e:
            logger.error(f"[AUDIT] Failed to list tables: {str(e)}")
            raise

    async def get_ingestion_volume(
        self,
        resource_group: str,
        workspace_name: str,
        days_lookback: int = 30
    ) -> Dict[str, float]:
        """
        Query Usage table to get ingestion volume per table (GB/day).

        Returns:
            Dictionary mapping table_name -> gb_per_day
        """
        try:
            logger.info(
                f"[AUDIT] Fetching ingestion volume for {days_lookback} days"
            )

            # KQL query to get ingestion per table
            kql_query = f"""
            Usage
            | where TimeGenerated >= ago({days_lookback}d)
            | where DataType != "Usage"
            | summarize TotalGB = sum(Quantity) / 1000 by DataType
            | extend AvgGBPerDay = TotalGB / {days_lookback}
            | project TableName=DataType, AvgGBPerDay
            """

            # Run the query
            workspace_id = f"/subscriptions/{settings.AZURE_SUBSCRIPTION_ID}/resourcegroups/{resource_group}/providers/microsoft.operationalinsights/workspaces/{workspace_name}"

            response = self.logs_query_client.query_workspace(
                workspace_id=workspace_id,
                query=kql_query,
                timespan=timedelta(days=days_lookback)
            )

            # Parse results
            ingestion_data = {}
            if response.tables:
                for row in response.tables[0].rows:
                    table_name = row[0]
                    avg_gb_per_day = float(row[1]) if row[1] is not None else 0.0
                    ingestion_data[table_name] = avg_gb_per_day

            logger.info(f"[AUDIT] Ingestion data fetched for {len(ingestion_data)} tables")
            return ingestion_data

        except Exception as e:
            logger.error(f"[AUDIT] Failed to get ingestion volume: {str(e)}")
            raise

    async def list_analytics_rules(
        self, resource_group: str, workspace_name: str
    ) -> List[AnalyticsRule]:
        """
        Fetch all analytics rules (Scheduled, NRT) from workspace.

        Returns:
            List of analytics rules with KQL queries
        """
        try:
            logger.info(f"[AUDIT] Fetching analytics rules")

            rules = []

            # Get all alert rules from Sentinel
            alert_rules = self.sentinel_client.alert_rules.list(
                resource_group_name=resource_group,
                operational_insights_resource_id=f"/subscriptions/{settings.AZURE_SUBSCRIPTION_ID}/resourcegroups/{resource_group}/providers/microsoft.operationalinsights/workspaces/{workspace_name}"
            )

            rule_count = 0
            for rule in alert_rules:
                try:
                    # Extract rule type
                    rule_type = type(rule).__name__

                    # Extract KQL query if present
                    kql_query = getattr(rule, 'query', '')

                    if kql_query:
                        rules.append(
                            AnalyticsRule(
                                rule_id=rule.id,
                                rule_name=rule.name,
                                rule_type=rule_type,
                                kql_query=kql_query,
                                enabled=getattr(rule, 'enabled', False),
                                tables_referenced=[]  # Will be populated by KQL parser
                            )
                        )
                        rule_count += 1

                except Exception as e:
                    logger.warning(f"[AUDIT] Failed to parse rule {rule.name}: {str(e)}")
                    continue

            logger.info(f"[AUDIT] Successfully listed {rule_count} analytics rules")
            return rules

        except Exception as e:
            logger.error(f"[AUDIT] Failed to list analytics rules: {str(e)}")
            raise

    async def list_workbooks(
        self, resource_group: str, workspace_name: str
    ) -> List[Workbook]:
        """
        Fetch all workbooks and extract KQL queries.

        Returns:
            List of workbooks with KQL queries
        """
        try:
            logger.info("[AUDIT] Fetching workbooks")

            workbooks = []

            # Get all workbooks from Sentinel
            workbook_list = self.sentinel_client.workbook_templates.list(
                resource_group_name=resource_group
            )

            workbook_count = 0
            for wb in workbook_list:
                try:
                    # Extract KQL queries from workbook (simplified)
                    kql_queries = self._extract_kql_from_workbook(wb)

                    workbooks.append(
                        Workbook(
                            workbook_id=wb.id,
                            workbook_name=wb.name,
                            kql_queries=kql_queries,
                            tables_referenced=[]  # Will be populated by KQL parser
                        )
                    )
                    workbook_count += 1

                except Exception as e:
                    logger.warning(f"[AUDIT] Failed to parse workbook {wb.name}: {str(e)}")
                    continue

            logger.info(f"[AUDIT] Successfully listed {workbook_count} workbooks")
            return workbooks

        except Exception as e:
            logger.error(f"[AUDIT] Failed to list workbooks: {str(e)}")
            raise

    async def list_hunt_queries(
        self, resource_group: str, workspace_name: str
    ) -> List[HuntQuery]:
        """
        Fetch all hunt/saved queries.

        Returns:
            List of hunt queries with KQL
        """
        try:
            logger.info("[AUDIT] Fetching hunt queries")

            hunt_queries = []

            # Get all saved searches (hunt queries)
            saved_searches = self.log_analytics_client.saved_searches.list_by_workspace(
                resource_group_name=resource_group,
                workspace_name=workspace_name
            )

            query_count = 0
            for search in saved_searches:
                try:
                    kql_query = getattr(search, 'query', '')

                    if kql_query:
                        hunt_queries.append(
                            HuntQuery(
                                query_id=search.id,
                                query_name=search.name,
                                kql_query=kql_query,
                                tables_referenced=[]  # Will be populated by KQL parser
                            )
                        )
                        query_count += 1

                except Exception as e:
                    logger.warning(f"[AUDIT] Failed to parse hunt query {search.name}: {str(e)}")
                    continue

            logger.info(f"[AUDIT] Successfully listed {query_count} hunt queries")
            return hunt_queries

        except Exception as e:
            logger.error(f"[AUDIT] Failed to list hunt queries: {str(e)}")
            raise

    async def list_data_connectors(
        self, resource_group: str, workspace_name: str
    ) -> List[DataConnector]:
        """
        List all active data connectors and their table mappings.

        Returns:
            List of connectors with tables they feed
        """
        try:
            logger.info("[AUDIT] Fetching data connectors")

            connectors = []

            # Get all data connectors from Sentinel
            connector_list = self.sentinel_client.data_connectors.list(
                resource_group_name=resource_group,
                operational_insights_resource_id=f"/subscriptions/{settings.AZURE_SUBSCRIPTION_ID}/resourcegroups/{resource_group}/providers/microsoft.operationalinsights/workspaces/{workspace_name}"
            )

            connector_count = 0
            for connector in connector_list:
                try:
                    # Extract connector type and table mappings
                    connector_type = type(connector).__name__
                    tables = self._get_connector_tables(connector)

                    connectors.append(
                        DataConnector(
                            connector_name=connector.name,
                            connector_id=connector.id,
                            connector_type=connector_type,
                            tables_fed=tables
                        )
                    )
                    connector_count += 1

                except Exception as e:
                    logger.warning(f"[AUDIT] Failed to parse connector {connector.name}: {str(e)}")
                    continue

            logger.info(f"[AUDIT] Successfully listed {connector_count} data connectors")
            return connectors

        except Exception as e:
            logger.error(f"[AUDIT] Failed to list data connectors: {str(e)}")
            raise

    # ===== HELPER METHODS =====

    def _get_table_tier(self, table) -> TierType:
        """Extract tier from table object"""
        tier_str = getattr(table.properties, 'retention_in_days_type', 'Hot')
        if 'Archive' in tier_str:
            return TierType.ARCHIVE
        elif 'Basic' in tier_str:
            return TierType.BASIC
        return TierType.HOT

    def _get_table_retention(self, table) -> int:
        """Extract retention days from table object"""
        return getattr(table.properties, 'retention_in_days', 30)

    def _extract_kql_from_workbook(self, workbook) -> List[str]:
        """Extract KQL queries from workbook JSON"""
        # Simplified - in production would parse workbook JSON structure
        return []

    def _get_connector_tables(self, connector) -> List[str]:
        """Extract table names that connector feeds"""
        # Simplified - in production would parse connector configuration
        return []


# ===== SINGLETON INSTANCE =====
azure_api_service = AzureApiService()
