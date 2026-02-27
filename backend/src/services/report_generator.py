"""
Report Generator Service

Assembles structured optimization reports from agent analysis results.
All outputs validated against Pydantic schemas.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
from collections import defaultdict

from src.models.schemas import (
    Report, ReportSummary, TableRecommendation, ConnectorCoverageItem,
    ReportWarning, ExecutionMetadata, TierType, ConfidenceLevel,
    AnalyticsRule, DataConnector, TableIngestionData, KqlParseResult
)
from src.services.cost_calculator import cost_calculator

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate optimization reports"""

    @staticmethod
    def generate_report(
        job_id: str,
        workspace_id: str,
        workspace_name: str,
        tables: List[TableIngestionData],
        rules: List[AnalyticsRule],
        ingestion_data: Dict[str, float],
        connectors: List[DataConnector],
        kql_parse_results: List[KqlParseResult],
        agent_tokens_used: int,
        agent_max_tokens: int,
        agent_run_seconds: float
    ) -> Report:
        """
        Generate optimization report.

        Args:
            job_id: Audit job ID
            workspace_id: Sentinel workspace ID
            workspace_name: Workspace display name
            tables: All tables in workspace
            rules: All analytics rules
            ingestion_data: Ingestion GB/day per table
            connectors: All data connectors
            kql_parse_results: KQL parsing results
            agent_tokens_used: Tokens consumed by agent
            agent_max_tokens: Max tokens allowed
            agent_run_seconds: Agent execution time

        Returns:
            Assembled Report object
        """
        try:
            logger.info(f"[REPORT] Generating report for job {job_id}")

            # Build table usage map from rules
            table_usage_map = ReportGenerator._build_table_usage_map(rules, kql_parse_results)

            # Categorize tables by usage and recommendations
            archive_candidates = []
            low_usage_candidates = []
            active_tables = []

            for table in tables:
                usage_count = len(table_usage_map.get(table.table_name, []))
                ingestion_gb_day = ingestion_data.get(table.table_name, 0.0)

                # Determine recommendation
                if usage_count == 0:
                    # No rule coverage = HIGH confidence archive candidate
                    confidence = ConfidenceLevel.HIGH
                    parsing_confidence = 1.0
                    recommendation_list = archive_candidates

                elif usage_count <= 2:
                    # Low coverage = MEDIUM confidence
                    confidence = ConfidenceLevel.MEDIUM
                    parsing_confidence = 0.7
                    recommendation_list = low_usage_candidates

                else:
                    # Active coverage = DO NOT TOUCH
                    confidence = ConfidenceLevel.HIGH
                    parsing_confidence = 1.0
                    recommendation_list = active_tables

                # Calculate costs
                costs = cost_calculator.calculate_table_costs(
                    ingestion_gb_day,
                    table.current_tier,
                    "Archive"
                )

                # Build recommendation
                rec = TableRecommendation(
                    table_name=table.table_name,
                    current_tier=table.current_tier,
                    ingestion_gb_per_day=round(ingestion_gb_day, 4),
                    ingestion_gb_per_month=round(ingestion_gb_day * 30, 2),
                    rule_coverage_count=usage_count,
                    rule_names=table_usage_map.get(table.table_name, [])[:5],  # Top 5
                    confidence=confidence,
                    parsing_confidence=parsing_confidence,
                    monthly_cost_hot=costs["monthly_cost_hot"],
                    monthly_cost_archive=costs["monthly_cost_archive"],
                    monthly_savings=costs["monthly_savings"],
                    annual_savings=costs["annual_savings"],
                    notes=ReportGenerator._generate_notes(
                        table.table_name, usage_count, ingestion_gb_day, table.retention_days
                    )
                )

                recommendation_list.append(rec)

            # Sort by savings
            archive_candidates.sort(key=lambda x: x.annual_savings, reverse=True)
            low_usage_candidates.sort(key=lambda x: x.annual_savings, reverse=True)
            active_tables.sort(key=lambda x: x.annual_savings, reverse=True)

            # Build connector coverage map
            connector_coverage = ReportGenerator._build_connector_coverage(
                connectors, table_usage_map
            )

            # Identify warnings
            warnings = ReportGenerator._generate_warnings(
                tables, kql_parse_results, archive_candidates
            )

            # Calculate summary
            summary = ReportGenerator._calculate_summary(
                tables, archive_candidates, low_usage_candidates, active_tables
            )

            # Build metadata
            metadata = ExecutionMetadata(
                agent_run_timestamp=datetime.utcnow(),
                agent_completion_time_seconds=agent_run_seconds,
                kql_parsing_success_rate=ReportGenerator._calculate_parse_success_rate(kql_parse_results),
                tables_analyzed=len(tables),
                rules_analyzed=len(rules),
                workbooks_analyzed=0,  # Set by caller
                hunt_queries_analyzed=0,  # Set by caller
                agent_tokens_used=agent_tokens_used,
                agent_tokens_limit=agent_max_tokens
            )

            # Assemble report
            report = Report(
                job_id=job_id,
                workspace_id=workspace_id,
                workspace_name=workspace_name,
                timestamp=datetime.utcnow(),
                summary=summary,
                archive_candidates=archive_candidates,
                low_usage_candidates=low_usage_candidates,
                active_tables=active_tables,
                connector_coverage=connector_coverage,
                warnings=warnings,
                metadata=metadata
            )

            logger.info(
                f"[REPORT] Report generated: {len(archive_candidates)} archive candidates, "
                f"${summary.total_annual_savings:,.0f} potential annual savings"
            )

            return report

        except Exception as e:
            logger.error(f"[REPORT] Report generation failed: {str(e)}")
            raise

    @staticmethod
    def _build_table_usage_map(
        rules: List[AnalyticsRule], kql_parse_results: List[KqlParseResult]
    ) -> Dict[str, List[str]]:
        """Build mapping of tables to rules that reference them"""
        usage_map = defaultdict(list)

        for rule, parse_result in zip(rules, kql_parse_results):
            if parse_result.success:
                for table in parse_result.tables:
                    usage_map[table].append(rule.rule_name)

        return dict(usage_map)

    @staticmethod
    def _build_connector_coverage(
        connectors: List[DataConnector], table_usage_map: Dict[str, List[str]]
    ) -> List[ConnectorCoverageItem]:
        """Build connector to table coverage mapping"""
        coverage_items = []

        for connector in connectors:
            tables_with_coverage = sum(
                1 for table in connector.tables_fed if table in table_usage_map
            )

            coverage_items.append(
                ConnectorCoverageItem(
                    connector_name=connector.connector_name,
                    connector_type=connector.connector_type,
                    tables_fed=connector.tables_fed,
                    tables_with_coverage=tables_with_coverage,
                    tables_without_coverage=len(connector.tables_fed) - tables_with_coverage
                )
            )

        return coverage_items

    @staticmethod
    def _generate_warnings(
        tables: List[TableIngestionData],
        kql_parse_results: List[KqlParseResult],
        archive_candidates: List[TableRecommendation]
    ) -> List[ReportWarning]:
        """Generate warnings and manual review items"""
        warnings = []

        # Flag low-confidence parsing
        for result in kql_parse_results:
            if result.parsing_confidence < 0.5 and not result.success:
                warnings.append(
                    ReportWarning(
                        warning_type="COMPLEX_KQL",
                        table_name="N/A",
                        description="Complex KQL with functions/aliases detected - manual review recommended",
                        recommendation="Review the rule manually to verify table extraction"
                    )
                )

        # Flag high-retention tables being archived
        for candidate in archive_candidates:
            if candidate.current_tier == TierType.HOT and candidate.monthly_cost_hot > 100:
                warnings.append(
                    ReportWarning(
                        warning_type="HIGH_COST_ARCHIVE",
                        table_name=candidate.table_name,
                        description=f"High-cost table (${candidate.monthly_cost_hot:.2f}/month) with no rule coverage",
                        recommendation="Verify no external systems depend on this table before archiving"
                    )
                )

        return warnings

    @staticmethod
    def _calculate_summary(
        tables: List[TableIngestionData],
        archive_candidates: List[TableRecommendation],
        low_usage_candidates: List[TableRecommendation],
        active_tables: List[TableRecommendation]
    ) -> ReportSummary:
        """Calculate executive summary"""
        # Total ingestion
        total_gb_month = sum(r.ingestion_gb_per_month for r in (archive_candidates + low_usage_candidates + active_tables))

        # Total costs
        total_cost_hot = sum(r.monthly_cost_hot for r in (archive_candidates + low_usage_candidates + active_tables))
        total_cost_archive = sum(r.monthly_cost_archive for r in (archive_candidates + low_usage_candidates + active_tables))
        total_monthly_savings = total_cost_hot - total_cost_archive
        total_annual_savings = total_monthly_savings * 12

        # Tier breakdown
        tier_breakdown = {
            "Hot": len([r for r in (archive_candidates + low_usage_candidates + active_tables) if r.current_tier == TierType.HOT]),
            "Basic": len([r for r in (archive_candidates + low_usage_candidates + active_tables) if r.current_tier == TierType.BASIC]),
            "Archive": len([r for r in (archive_candidates + low_usage_candidates + active_tables) if r.current_tier == TierType.ARCHIVE])
        }

        # Confidence breakdown
        confidence_breakdown = {
            "HIGH": len([r for r in (archive_candidates + low_usage_candidates + active_tables) if r.confidence == ConfidenceLevel.HIGH]),
            "MEDIUM": len([r for r in (archive_candidates + low_usage_candidates + active_tables) if r.confidence == ConfidenceLevel.MEDIUM]),
            "LOW": len([r for r in (archive_candidates + low_usage_candidates + active_tables) if r.confidence == ConfidenceLevel.LOW])
        }

        return ReportSummary(
            total_tables_analyzed=len(tables),
            total_ingestion_gb_per_month=round(total_gb_month, 2),
            total_monthly_cost_hot=round(total_cost_hot, 2),
            total_monthly_cost_archive=round(total_cost_archive, 2),
            total_monthly_savings=round(total_monthly_savings, 2),
            total_annual_savings=round(total_annual_savings, 2),
            tables_by_tier=tier_breakdown,
            tables_by_confidence=confidence_breakdown
        )

    @staticmethod
    def _generate_notes(
        table_name: str, usage_count: int, ingestion_gb_day: float, retention_days: int
    ) -> str:
        """Generate notes for a table recommendation"""
        notes = []

        if usage_count == 0:
            notes.append("No analytics rules reference this table")
        elif usage_count <= 2:
            notes.append(f"Only {usage_count} rule(s) reference this table")

        if ingestion_gb_day < 0.01:
            notes.append("Minimal ingestion volume")
        elif ingestion_gb_day > 10:
            notes.append(f"High ingestion: {ingestion_gb_day:.1f} GB/day")

        if retention_days < 30:
            notes.append(f"Short retention: {retention_days} days")

        return "; ".join(notes) if notes else "Archive candidate for cost optimization"

    @staticmethod
    def _calculate_parse_success_rate(kql_parse_results: List[KqlParseResult]) -> float:
        """Calculate KQL parsing success rate"""
        if not kql_parse_results:
            return 0.0

        success_count = sum(1 for r in kql_parse_results if r.success)
        return success_count / len(kql_parse_results)


# ===== SINGLETON INSTANCE =====
report_generator = ReportGenerator()
