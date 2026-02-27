"""
KQL Parser Service

Extracts table names from KQL queries using:
1. AST parsing (python-kql library) - High confidence
2. Regex fallback - Medium/Low confidence

All parsing results include confidence scores and parsing method.
"""

import re
import logging
from typing import List, Set, Tuple
from enum import Enum

from src.models.schemas import KqlParseResult, ConfidenceLevel

logger = logging.getLogger(__name__)


class KqlParser:
    """KQL query parser for table extraction"""

    # Common table name patterns in Sentinel
    COMMON_TABLES = {
        "SecurityEvent", "SigninLogs", "AuditLogs", "AADManagedIdentitySignInLogs",
        "AADNonInteractiveUserSignInLogs", "AADServicePrincipalSignInLogs",
        "AADUserRiskEvents", "AADIdentityProtectionAllRiskEvents",
        "CommonSecurityLog", "Syslog", "CiscoASAConnection", "CiscoASADns",
        "CiscoASAFirewall", "Fortinet_FortiGate_log", "PaloAltoNetworks_PAN_OS",
        "WindowsEvent", "WaaSUpdateStatus", "Update", "UpdateRunProgress",
        "OfficeActivity", "DnsEvents", "HTTPProxy", "URLFilter",
        "HealthStateChangeEvents", "WAFLogs", "AppServiceHTTPLogs",
        "ApiManagementGatewayLogs", "ApplicationInsights", "ExceptionEvents",
        "Heartbeat", "Perf", "ContainerLog", "ContainerLogV2",
        "Kubernetes Events", "KubeEvents", "KubeNodeInventory", "KubePodInventory",
        "AzureActivity", "AzureDiagnostics", "StorageBlob", "StorageQueue",
        "StorageTable", "StorageFile"
    }

    # Regex patterns for table references
    REGEX_PATTERNS = [
        # Simple table reference: TableName
        (r'\b([A-Z][a-zA-Z0-9_]*)\b(?=\s*[\|\;]|$)', 1.0),
        # workspace() qualified: workspace("name").TableName
        (r'workspace\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\.\s*([A-Z][a-zA-Z0-9_]*)', 0.9),
        # union statements: union Table1, Table2, ...
        (r'union\s+\(?([A-Z][a-zA-Z0-9_]*(?:\s*,\s*[A-Z][a-zA-Z0-9_]*)*)\)?', 0.85),
        # datatable references
        (r'datatable\s*\([^)]+\)\s*\[\s*([A-Z][a-zA-Z0-9_]*)', 0.75),
    ]

    def parse(self, kql_query: str) -> KqlParseResult:
        """
        Parse KQL query and extract table names.

        Strategy:
        1. Try AST parsing (python-kql)
        2. Fall back to regex matching
        3. Return results with confidence scores

        Args:
            kql_query: Raw KQL query string

        Returns:
            KqlParseResult with extracted tables and confidence
        """
        if not kql_query or not kql_query.strip():
            return KqlParseResult(
                tables=[],
                confidence=ConfidenceLevel.HIGH,
                parsing_method="REGEX",
                success=False,
                error_message="Empty KQL query"
            )

        try:
            # Attempt 1: Try python-kql AST parsing
            tables = self._parse_with_ast(kql_query)
            if tables:
                logger.debug(f"[KQL] AST parsing found {len(tables)} tables")
                return KqlParseResult(
                    tables=list(tables),
                    confidence=ConfidenceLevel.HIGH,
                    parsing_method="AST",
                    success=True
                )

        except Exception as e:
            logger.debug(f"[KQL] AST parsing failed: {str(e)}")

        try:
            # Attempt 2: Regex fallback
            tables, confidence = self._parse_with_regex(kql_query)
            if tables:
                logger.debug(f"[KQL] Regex parsing found {len(tables)} tables (confidence: {confidence})")
                return KqlParseResult(
                    tables=list(tables),
                    confidence=confidence,
                    parsing_method="REGEX",
                    success=True
                )

        except Exception as e:
            logger.error(f"[KQL] Regex parsing failed: {str(e)}")

        # No tables found
        return KqlParseResult(
            tables=[],
            confidence=ConfidenceLevel.LOW,
            parsing_method="REGEX",
            success=False,
            error_message="No tables extracted"
        )

    def _parse_with_ast(self, kql_query: str) -> Set[str]:
        """
        Parse KQL using python-kql AST parser.

        Returns:
            Set of table names found
        """
        try:
            # This is a simplified implementation
            # In production, use the actual python-kql library
            # from kql_ast_parser import Parser
            # parser = Parser()
            # ast = parser.parse(kql_query)
            # return self._extract_tables_from_ast(ast)

            # For now, just use regex as fallback
            return set()

        except Exception as e:
            logger.debug(f"[KQL] AST parsing error: {str(e)}")
            return set()

    def _parse_with_regex(self, kql_query: str) -> Tuple[Set[str], ConfidenceLevel]:
        """
        Parse KQL using regex patterns.

        Returns:
            Tuple of (tables set, confidence level)
        """
        tables = set()
        max_confidence = ConfidenceLevel.LOW

        # Clean up query (remove comments, normalize whitespace)
        cleaned_query = self._clean_kql(kql_query)

        # Try each regex pattern
        for pattern, base_confidence in self.REGEX_PATTERNS:
            try:
                matches = re.findall(pattern, cleaned_query, re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    # Handle tuple returns from groups
                    if isinstance(match, tuple):
                        for group in match:
                            if group and group.strip():
                                table_name = group.strip().split()[0]  # Get first word if multiple
                                if self._is_valid_table_name(table_name):
                                    tables.add(table_name)
                    else:
                        if match and match.strip():
                            table_name = match.strip().split()[0]
                            if self._is_valid_table_name(table_name):
                                tables.add(table_name)

                    if base_confidence > max_confidence:
                        max_confidence = ConfidenceLevel.HIGH if base_confidence > 0.8 else ConfidenceLevel.MEDIUM

            except Exception as e:
                logger.debug(f"[KQL] Regex pattern failed: {str(e)}")

        # Adjust confidence based on findings
        if not tables:
            return set(), ConfidenceLevel.LOW
        elif len(tables) == 1:
            return tables, ConfidenceLevel.MEDIUM
        else:
            return tables, max_confidence if max_confidence else ConfidenceLevel.MEDIUM

    def _clean_kql(self, kql_query: str) -> str:
        """Clean KQL query for parsing"""
        # Remove comments
        kql = re.sub(r'//.*$', '', kql_query, flags=re.MULTILINE)
        kql = re.sub(r'/\*.*?\*/', '', kql, flags=re.DOTALL)

        # Normalize whitespace
        kql = re.sub(r'\s+', ' ', kql)

        return kql.strip()

    def _is_valid_table_name(self, name: str) -> bool:
        """Check if string is a valid table name"""
        if not name:
            return False

        # Table names should:
        # - Start with letter or underscore
        # - Contain alphanumeric and underscores only
        # - Not be a KQL keyword
        if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name):
            return False

        # Check against KQL keywords
        kql_keywords = {
            'where', 'project', 'summarize', 'count', 'sum', 'avg', 'min', 'max',
            'sort', 'limit', 'take', 'union', 'join', 'let', 'print', 'extend',
            'distinct', 'top', 'range', 'as', 'by', 'on', 'with', 'between',
            'in', 'and', 'or', 'not', 'has', 'contains', 'startswith', 'endswith',
            'matches', 'regex', 'timespan', 'ago', 'now', 'datetime',
            'strcat', 'tolower', 'toupper', 'split', 'parse'
        }

        return name.lower() not in kql_keywords

    def batch_parse(self, kql_queries: List[str]) -> List[KqlParseResult]:
        """
        Parse multiple KQL queries.

        Args:
            kql_queries: List of KQL query strings

        Returns:
            List of parse results
        """
        logger.info(f"[KQL] Batch parsing {len(kql_queries)} queries")

        results = []
        for i, query in enumerate(kql_queries):
            try:
                result = self.parse(query)
                results.append(result)
            except Exception as e:
                logger.error(f"[KQL] Query {i} parsing failed: {str(e)}")
                results.append(
                    KqlParseResult(
                        tables=[],
                        confidence=ConfidenceLevel.LOW,
                        parsing_method="REGEX",
                        success=False,
                        error_message=str(e)
                    )
                )

        # Calculate overall success rate
        success_count = sum(1 for r in results if r.success)
        success_rate = success_count / len(results) if results else 0.0

        logger.info(f"[KQL] Batch parse completed: {success_rate:.1%} success rate")

        return results


# ===== SINGLETON INSTANCE =====
kql_parser = KqlParser()
