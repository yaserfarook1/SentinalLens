"""
Pytest configuration and fixtures
"""

import pytest
import os
from pathlib import Path


@pytest.fixture(scope="session")
def test_data_dir():
    """Return path to test data directory"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_kql_queries():
    """Sample KQL queries for testing"""
    return {
        "simple": "SecurityEvent | count",
        "union": "union SecurityEvent, SigninLogs | where TimeGenerated > ago(7d)",
        "workspace_qualified": 'workspace("prod").SecurityEvent | count',
        "complex": """
        SecurityEvent
        | where EventID in (4688, 4689)
        | summarize count() by Computer
        | where count_ > 100
        """,
        "with_functions": """
        SecurityEvent
        | extend ParsedEvent = parse_json(ExtendedProperties)
        | where tostring(ParsedEvent.EventID) == "4625"
        """,
    }


@pytest.fixture
def sample_ingestion_data():
    """Sample ingestion data for cost calculations"""
    return {
        "SecurityEvent": 50.0,  # 50 GB/day
        "SigninLogs": 25.0,     # 25 GB/day
        "AuditLogs": 10.0,      # 10 GB/day
        "UnusedTable": 0.01,    # Minimal ingestion
    }


@pytest.fixture
def sample_tables_data():
    """Sample table ingestion data"""
    from src.models.schemas import TableIngestionData, TierType

    return [
        TableIngestionData(
            table_name="SecurityEvent",
            current_tier=TierType.HOT,
            retention_days=90,
            ingestion_gb_per_day=50.0,
            ingestion_gb_per_month=1500.0
        ),
        TableIngestionData(
            table_name="SigninLogs",
            current_tier=TierType.HOT,
            retention_days=30,
            ingestion_gb_per_day=25.0,
            ingestion_gb_per_month=750.0
        ),
        TableIngestionData(
            table_name="UnusedTable",
            current_tier=TierType.HOT,
            retention_days=7,
            ingestion_gb_per_day=0.01,
            ingestion_gb_per_month=0.3
        ),
    ]


@pytest.fixture
def sample_analytics_rules():
    """Sample analytics rules"""
    from src.models.schemas import AnalyticsRule

    return [
        AnalyticsRule(
            rule_id="rule-1",
            rule_name="Failed Login Attempts",
            rule_type="Scheduled",
            kql_query="SecurityEvent | where EventID == 4625 | count",
            enabled=True,
            tables_referenced=["SecurityEvent"],
            parsing_confidence=1.0
        ),
        AnalyticsRule(
            rule_id="rule-2",
            rule_name="Successful Logins",
            rule_type="Scheduled",
            kql_query="SigninLogs | where ResultType == 0 | count",
            enabled=True,
            tables_referenced=["SigninLogs"],
            parsing_confidence=1.0
        ),
    ]


@pytest.fixture
def sample_connectors():
    """Sample data connectors"""
    from src.models.schemas import DataConnector

    return [
        DataConnector(
            connector_name="Azure AD",
            connector_id="connector-1",
            connector_type="AzureADConnector",
            tables_fed=["SigninLogs", "AuditLogs"]
        ),
        DataConnector(
            connector_name="Windows Security",
            connector_id="connector-2",
            connector_type="WindowsSecurityConnector",
            tables_fed=["SecurityEvent"]
        ),
    ]


@pytest.fixture
def sample_parse_results():
    """Sample KQL parse results"""
    from src.models.schemas import KqlParseResult, ConfidenceLevel

    return [
        KqlParseResult(
            tables=["SecurityEvent"],
            confidence=ConfidenceLevel.HIGH,
            parsing_method="REGEX",
            success=True
        ),
        KqlParseResult(
            tables=["SigninLogs"],
            confidence=ConfidenceLevel.HIGH,
            parsing_method="REGEX",
            success=True
        ),
        KqlParseResult(
            tables=[],
            confidence=ConfidenceLevel.LOW,
            parsing_method="REGEX",
            success=False,
            error_message="No tables found"
        ),
    ]


# Configure pytest
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow"
    )


# Autouse fixtures
@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests"""
    # This ensures tests don't interfere with each other
    yield
