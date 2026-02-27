"""
Unit tests for KQL parser
"""

import pytest
from src.services.kql_parser import kql_parser
from src.models.schemas import ConfidenceLevel


class TestKqlParser:
    """Test KQL parsing functionality"""

    def test_simple_table_reference(self):
        """Test parsing simple table reference"""
        kql = "SecurityEvent | where EventID == 4625"
        result = kql_parser.parse(kql)

        assert result.success
        assert "SecurityEvent" in result.tables
        assert result.parsing_method == "REGEX"

    def test_multiple_tables_union(self):
        """Test parsing union statement"""
        kql = "union SecurityEvent, SigninLogs | where TimeGenerated > ago(7d)"
        result = kql_parser.parse(kql)

        assert result.success
        assert "SecurityEvent" in result.tables or "SigninLogs" in result.tables
        assert result.confidence in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM]

    def test_workspace_qualified_table(self):
        """Test parsing workspace-qualified table reference"""
        kql = 'workspace("prod-workspace").SecurityEvent | count'
        result = kql_parser.parse(kql)

        assert result.success
        assert "SecurityEvent" in result.tables

    def test_empty_query(self):
        """Test empty KQL query"""
        result = kql_parser.parse("")

        assert not result.success
        assert len(result.tables) == 0
        assert result.confidence == ConfidenceLevel.HIGH  # Empty is confidently not valid

    def test_kql_with_comments(self):
        """Test KQL with comments"""
        kql = """
        // This is a comment
        SecurityEvent
        | where EventID == 4625
        | count  // Count failed logins
        """
        result = kql_parser.parse(kql)

        assert result.success
        assert "SecurityEvent" in result.tables

    def test_batch_parsing(self):
        """Test batch parsing multiple queries"""
        queries = [
            "SecurityEvent | count",
            "SigninLogs | where ResultType == 0",
            "AuditLogs | where OperationName == 'Create'"
        ]

        results = kql_parser.batch_parse(queries)

        assert len(results) == 3
        assert results[0].success
        assert "SecurityEvent" in results[0].tables

    def test_complex_kql_with_functions(self):
        """Test complex KQL with functions (lower confidence)"""
        kql = """
        SecurityEvent
        | extend ParsedEvent = parse_json(ExtendedProperties)
        | where tostring(ParsedEvent.EventID) == "4625"
        """
        result = kql_parser.parse(kql)

        # Should still find SecurityEvent despite complexity
        assert "SecurityEvent" in result.tables

    def test_invalid_table_names_excluded(self):
        """Test that KQL keywords are not parsed as tables"""
        kql = "where EventID == 4625 | union | select | count"
        result = kql_parser.parse(kql)

        # Should not include KQL keywords
        assert "where" not in result.tables
        assert "union" not in result.tables
        assert "select" not in result.tables

    def test_real_world_rule_query(self):
        """Test real-world analytics rule query"""
        kql = """
        SecurityEvent
        | where EventID in (4688, 4689)
        | summarize count() by Computer, Process, Account
        | where count_ > 100
        """
        result = kql_parser.parse(kql)

        assert result.success
        assert "SecurityEvent" in result.tables
        assert result.parsing_confidence > 0.5
