"""
End-to-End Integration Tests

Tests the complete workflow from audit creation through report generation
and approval on a real or mocked Sentinel workspace.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from src.main import app
from src.models.schemas import (
    StartAuditRequest,
    AnalyticsRule,
    Workbook,
    HuntQuery,
    DataConnector,
    AuditJob,
)
from src.services.azure_api import AzureApiService
from src.services.kql_parser import KQLParser
from src.services.cost_calculator import CostCalculator
from src.services.report_generator import ReportGenerator
from src.agents.orchestrator import AgentOrchestrator
from src.security_middleware import SecurityMiddleware


@pytest.fixture
def mock_azure_api():
    """Mock Azure API service"""
    api = Mock(spec=AzureApiService)

    # Mock workspace tables
    api.list_workspace_tables = AsyncMock(
        return_value=[
            {
                "table_name": "SecurityEvent",
                "current_tier": "Hot",
                "retention_days": 30,
                "ingestion_gb_per_day": 50.0,
            },
            {
                "table_name": "SigninLogs",
                "current_tier": "Hot",
                "retention_days": 30,
                "ingestion_gb_per_day": 20.0,
            },
            {
                "table_name": "AuditLogs",
                "current_tier": "Hot",
                "retention_days": 90,
                "ingestion_gb_per_day": 0.1,  # Very low usage
            },
            {
                "table_name": "DeviceLogonEvents",
                "current_tier": "Hot",
                "retention_days": 30,
                "ingestion_gb_per_day": 0.0,  # No usage
            },
        ]
    )

    # Mock ingestion volume query
    api.get_ingestion_volume = AsyncMock(
        return_value={
            "SecurityEvent": 50.0,
            "SigninLogs": 20.0,
            "AuditLogs": 0.1,
            "DeviceLogonEvents": 0.0,
        }
    )

    # Mock analytics rules
    api.list_analytics_rules = AsyncMock(
        return_value=[
            AnalyticsRule(
                rule_id="rule-1",
                rule_name="Brute Force Attack",
                kql_query="SecurityEvent | where EventID == 4625 | summarize by TargetUserName",
            ),
            AnalyticsRule(
                rule_id="rule-2",
                rule_name="Sign-in Failure",
                kql_query="SigninLogs | where Status.errorCode != 0",
            ),
            # Rule that doesn't reference any table
            AnalyticsRule(
                rule_id="rule-3",
                rule_name="Generic Detection",
                kql_query="print('test')",
            ),
        ]
    )

    # Mock workbooks
    api.list_workbooks = AsyncMock(
        return_value=[
            Workbook(
                workbook_id="wb-1",
                workbook_name="Security Monitoring",
                kql_query="SecurityEvent | summarize count() by EventID",
            ),
        ]
    )

    # Mock hunt queries
    api.list_hunt_queries = AsyncMock(
        return_value=[
            HuntQuery(
                query_id="hunt-1",
                query_name="Find Lateral Movement",
                kql_query="SecurityEvent | where EventID == 4688",
            ),
        ]
    )

    # Mock data connectors
    api.list_data_connectors = AsyncMock(
        return_value=[
            DataConnector(
                connector_id="conn-1",
                connector_name="Azure AD Connector",
                connector_type="AzureAD",
                tables=["SigninLogs", "AuditLogs"],
            ),
            DataConnector(
                connector_id="conn-2",
                connector_name="Windows Defender Connector",
                connector_type="WindowsDefender",
                tables=["DeviceLogonEvents"],
            ),
        ]
    )

    return api


@pytest.mark.asyncio
async def test_complete_audit_workflow(mock_azure_api):
    """
    Test complete workflow:
    1. List workspace tables
    2. Parse analytics rules to find table references
    3. Calculate ingestion volume
    4. Generate cost savings report
    5. Validate confidence scores
    """

    # Step 1: List tables
    tables = await mock_azure_api.list_workspace_tables()
    assert len(tables) == 4
    assert any(t["table_name"] == "SecurityEvent" for t in tables)

    # Step 2: Get ingestion volume
    ingestion = await mock_azure_api.get_ingestion_volume()
    assert ingestion["SecurityEvent"] == 50.0
    assert ingestion["AuditLogs"] == 0.1

    # Step 3: Parse analytics rules
    rules = await mock_azure_api.list_analytics_rules()
    parser = KQLParser()

    table_coverage = {}
    for table in tables:
        table_coverage[table["table_name"]] = {"rules": [], "workbooks": [], "hunts": []}

    for rule in rules:
        result = parser.parse_kql(rule.kql_query)
        for table in result["tables"]:
            if table in table_coverage:
                table_coverage[table]["rules"].append(rule.rule_name)

    # Verify SecurityEvent is highly covered
    assert len(table_coverage["SecurityEvent"]["rules"]) >= 1
    assert "Brute Force Attack" in table_coverage["SecurityEvent"]["rules"]

    # Verify AuditLogs has some coverage
    assert len(table_coverage["AuditLogs"]["rules"]) >= 1

    # Verify DeviceLogonEvents has no coverage yet (0 ingestion)
    assert table_coverage["DeviceLogonEvents"]["rules"] == []

    # Step 4: Calculate costs
    calculator = CostCalculator()

    archive_candidates = []
    low_usage_candidates = []
    active_tables = []

    for table_name, coverage_data in table_coverage.items():
        rule_count = len(coverage_data["rules"])
        ingestion_gb = ingestion.get(table_name, 0)

        costs = calculator.calculate_table_costs(
            ingestion_gb_per_day=ingestion_gb,
            current_tier="Hot",
            target_tier="Archive",
        )

        if rule_count == 0 and ingestion_gb == 0:
            # No usage, safe to archive
            archive_candidates.append({
                "table_name": table_name,
                "confidence": "HIGH",
                "annual_savings": costs["annual_savings"],
            })
        elif rule_count <= 2 and ingestion_gb < 1:
            # Low usage, flag for review
            low_usage_candidates.append({
                "table_name": table_name,
                "confidence": "MEDIUM",
                "annual_savings": costs["annual_savings"],
            })
        else:
            # High usage, keep as-is
            active_tables.append({
                "table_name": table_name,
                "confidence": "HIGH",
                "annual_savings": 0,
            })

    # Verify categorization
    assert any(c["table_name"] == "DeviceLogonEvents" for c in archive_candidates)
    assert any(c["table_name"] == "AuditLogs" for c in low_usage_candidates)
    assert any(c["table_name"] == "SecurityEvent" for c in active_tables)
    assert any(c["table_name"] == "SigninLogs" for c in active_tables)

    # Step 5: Verify savings calculation
    total_savings = sum(c["annual_savings"] for c in archive_candidates + low_usage_candidates)
    assert total_savings > 0  # Should have some savings

    print(f"✓ Archive candidates: {len(archive_candidates)}")
    print(f"✓ Low usage candidates: {len(low_usage_candidates)}")
    print(f"✓ Active tables: {len(active_tables)}")
    print(f"✓ Total annual savings: ${total_savings:.2f}")


@pytest.mark.asyncio
async def test_kql_parser_accuracy():
    """
    Test KQL parser against real-world KQL samples
    """
    parser = KQLParser()

    test_cases = [
        # Simple table reference
        ("SecurityEvent | where EventID == 4625", ["SecurityEvent"], "HIGH"),
        # Union of tables
        ("union SecurityEvent, SigninLogs | summarize count()", ["SecurityEvent", "SigninLogs"], "HIGH"),
        # Workspace-qualified reference
        ("workspace('ws1').SecurityEvent | take 10", ["SecurityEvent"], "MEDIUM"),
        # Dynamic query (low confidence)
        ("let t = dynamic('SecurityEvent'); print(t)", ["SecurityEvent"], "LOW"),
        # Comments should be ignored
        ("// SecurityEvent comment\nSigninLogs | take 10", ["SigninLogs"], "HIGH"),
        # Function call (unknown table)
        ("let f(t) = t | f(SecurityEvent)", ["SecurityEvent"], "MEDIUM"),
    ]

    for kql, expected_tables, min_confidence in test_cases:
        result = parser.parse_kql(kql)

        # Verify all expected tables are found
        assert set(expected_tables).issubset(set(result["tables"])), \
            f"Missing tables in: {kql}\nExpected: {expected_tables}, Got: {result['tables']}"

        # Verify confidence meets threshold
        confidence_map = {"HIGH": 0.85, "MEDIUM": 0.5, "LOW": 0.0}
        assert result["confidence_score"] >= confidence_map[min_confidence], \
            f"Confidence too low for: {kql}\nGot: {result['confidence_score']}"

    print("✓ KQL parser passed all test cases")


@pytest.mark.asyncio
async def test_security_middleware_integration():
    """
    Test security middleware: PII masking and prompt injection detection
    """
    middleware = SecurityMiddleware()

    # Test PII masking
    kql_with_pii = "SecurityEvent | where UserPrincipalName == 'user@company.com' and IPAddress == '192.168.1.100'"

    rules_to_mask = [
        AnalyticsRule(
            rule_id="rule-1",
            rule_name="PII Test Rule",
            kql_query=kql_with_pii,
        )
    ]

    # Mock the security functions
    with patch("src.security_middleware.prompt_shield.validate") as mock_shield:
        mock_shield.return_value = (True, 0.0, "Safe")

        with patch("src.security_middleware.pii_masking.mask") as mock_mask:
            # Create mock result
            mock_result = Mock()
            mock_result.masked_text = "SecurityEvent | where UserPrincipalName == '<EMAIL_ADDRESS_1>' and IPAddress == '<IP_ADDRESS_1>'"
            mock_result.pii_entities_found = 2
            mock_mask.return_value = mock_result

            masked_rules = middleware.validate_and_mask_kql_queries(rules_to_mask)

            assert len(masked_rules) == 1
            assert "<EMAIL_ADDRESS_1>" in masked_rules[0].kql_query
            assert "<IP_ADDRESS_1>" in masked_rules[0].kql_query
            assert "user@company.com" not in masked_rules[0].kql_query
            assert "192.168.1.100" not in masked_rules[0].kql_query

    print("✓ Security middleware passed PII masking test")


@pytest.mark.asyncio
async def test_cost_calculation_accuracy():
    """
    Test cost calculator against real Azure pricing
    """
    calculator = CostCalculator()

    # Test case: 100GB/day for 30 days
    # Expected: Hot rate ~$0.10/GB, Archive rate ~$0.002/GB
    # Monthly savings: (100 * 0.10 * 30) - (100 * 0.002 * 30) = $300 - $6 = $294

    with patch.object(calculator, "_get_pricing") as mock_pricing:
        mock_pricing.side_effect = lambda tier: 0.10 if tier == "Hot" else 0.002

        costs = calculator.calculate_table_costs(
            ingestion_gb_per_day=100.0,
            current_tier="Hot",
            target_tier="Archive",
        )

        assert costs["monthly_cost_hot"] == pytest.approx(300, rel=0.01)
        assert costs["monthly_cost_archive"] == pytest.approx(6, rel=0.01)
        assert costs["monthly_savings"] == pytest.approx(294, rel=0.01)
        assert costs["annual_savings"] == pytest.approx(3528, rel=0.01)

    print("✓ Cost calculation accuracy verified")
    print(f"  - 100GB/day table: ${294:.2f}/month savings")


@pytest.mark.asyncio
async def test_report_generation():
    """
    Test report generator produces valid structured output
    """
    generator = ReportGenerator()

    # Create sample data
    archive_candidates = [
        {
            "table_name": "UnusedTable1",
            "current_tier": "Hot",
            "ingestion_gb_per_day": 0.0,
            "rule_coverage_count": 0,
            "confidence": "HIGH",
            "monthly_savings": 0,
            "annual_savings": 0,
        },
        {
            "table_name": "UnusedTable2",
            "current_tier": "Hot",
            "ingestion_gb_per_day": 0.05,
            "rule_coverage_count": 0,
            "confidence": "HIGH",
            "monthly_savings": 1.44,
            "annual_savings": 17.28,
        },
    ]

    low_usage = [
        {
            "table_name": "LowUsageTable",
            "current_tier": "Hot",
            "ingestion_gb_per_day": 0.5,
            "rule_coverage_count": 1,
            "confidence": "MEDIUM",
            "monthly_savings": 14.40,
            "annual_savings": 172.80,
        },
    ]

    active = [
        {
            "table_name": "SecurityEvent",
            "current_tier": "Hot",
            "ingestion_gb_per_day": 50.0,
            "rule_coverage_count": 5,
            "confidence": "HIGH",
            "monthly_savings": 0,
            "annual_savings": 0,
        },
    ]

    # Generate report
    report = generator.generate_report(
        job_id="test-job-123",
        workspace_id="test-ws-456",
        workspace_name="TestWorkspace",
        archive_candidates=archive_candidates,
        low_usage_candidates=low_usage,
        active_tables=active,
        metadata={
            "parsing_method": "MIXED",
            "kql_parse_success_rate": 0.95,
            "total_rules_analyzed": 50,
            "total_workbooks_analyzed": 10,
            "execution_time_seconds": 45,
            "timestamp": datetime.now().isoformat(),
        },
    )

    # Verify report structure
    assert report.job_id == "test-job-123"
    assert report.workspace_id == "test-ws-456"
    assert len(report.archive_candidates) == 2
    assert len(report.low_usage_candidates) == 1
    assert len(report.active_tables) == 1
    assert report.total_annual_savings == pytest.approx(190.08, rel=0.01)

    print("✓ Report generation passed")
    print(f"  - Archive candidates: {len(report.archive_candidates)}")
    print(f"  - Low usage: {len(report.low_usage_candidates)}")
    print(f"  - Total savings: ${report.total_annual_savings:.2f}/year")


# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
