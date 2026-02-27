"""
Security Middleware - PII Masking & Prompt Shield Integration

Applies security controls to all data flowing through the agent:
- PII masking before LLM ingestion
- Prompt injection detection
- Audit logging for all sensitive operations
"""

import logging
from typing import Any, Dict, List, Optional
import json

from src.security import pii_masking, prompt_shield, data_sanitizer
from src.utils.logging import AuditLogger
from src.models.schemas import (
    AnalyticsRule, Workbook, HuntQuery, DataConnector
)

logger = logging.getLogger(__name__)


class SecurityMiddleware:
    """
    Applies security controls to agent data flows.

    Two-stage protection:
    1. Prompt Shield: Detect injection attempts
    2. Presidio Masking: Detect and mask PII
    """

    @staticmethod
    def validate_and_mask_kql_queries(
        rules: List[AnalyticsRule],
    ) -> List[AnalyticsRule]:
        """
        Validate and mask KQL queries before processing.

        Args:
            rules: List of analytics rules with KQL

        Returns:
            Rules with masked KQL queries
        """
        logger.info(f"[SECURITY] Validating and masking {len(rules)} KQL queries")

        masked_rules = []
        for rule in rules:
            try:
                # Step 1: Validate with Prompt Shield
                is_safe, risk_score, reason = prompt_shield.validate(rule.kql_query)

                if not is_safe:
                    logger.warning(
                        f"[SECURITY] KQL query rejected (injection risk): {rule.rule_name} - {reason}"
                    )
                    # Skip malicious rule
                    continue

                # Step 2: Mask PII in KQL
                mask_result = pii_masking.mask(rule.kql_query)

                # Update rule with masked KQL
                rule.kql_query = mask_result.masked_text

                masked_rules.append(rule)

                if mask_result.pii_entities_found > 0:
                    logger.info(
                        f"[SECURITY] Masked {mask_result.pii_entities_found} PII entities in rule: {rule.rule_name}"
                    )

            except Exception as e:
                logger.error(f"[SECURITY] Failed to process rule {rule.rule_name}: {str(e)}")
                continue

        logger.info(f"[SECURITY] Processed {len(masked_rules)}/{len(rules)} rules")
        return masked_rules

    @staticmethod
    def mask_connector_metadata(
        connectors: List[DataConnector],
    ) -> List[DataConnector]:
        """
        Mask PII in connector metadata.

        Args:
            connectors: List of data connectors

        Returns:
            Connectors with masked metadata
        """
        logger.info(f"[SECURITY] Masking {len(connectors)} connector metadata")

        masked_connectors = []
        for connector in connectors:
            try:
                # Mask connector name if it contains sensitive info
                mask_result = pii_masking.mask(connector.connector_name)
                connector.connector_name = mask_result.masked_text

                masked_connectors.append(connector)

                if mask_result.pii_entities_found > 0:
                    logger.info(
                        f"[SECURITY] Masked connector: {connector.connector_id}"
                    )

            except Exception as e:
                logger.error(
                    f"[SECURITY] Failed to process connector {connector.connector_id}: {str(e)}"
                )
                continue

        return masked_connectors

    @staticmethod
    def sanitize_report_output(report_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize report before returning to user.

        Ensures no raw credentials, tokens, or sensitive data leaks in output.

        Args:
            report_json: Full report dictionary

        Returns:
            Sanitized report
        """
        try:
            # Convert to JSON string for sanitization
            report_str = json.dumps(report_json, default=str)

            # Apply data sanitizer
            sanitized_str = data_sanitizer.sanitize_logs(report_str)

            # Convert back to dict
            sanitized_json = json.loads(sanitized_str)

            logger.info("[SECURITY] Report output sanitized")
            return sanitized_json

        except Exception as e:
            logger.error(f"[SECURITY] Report sanitization failed: {str(e)}")
            # Return original report if sanitization fails (fail safe)
            return report_json

    @staticmethod
    def log_security_event(
        event_type: str,
        severity: str,
        details: str,
        user_id: Optional[str] = None
    ):
        """
        Log security event for audit trail.

        Args:
            event_type: Type of security event (INJECTION_ATTEMPT, PII_MASKED, etc)
            severity: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
            details: Event details (no sensitive data)
            user_id: Optional user ID
        """
        log_entry = {
            "event_type": event_type,
            "severity": severity,
            "details": details
        }

        if user_id:
            log_entry["user_id"] = user_id

        if severity == "CRITICAL":
            logger.critical(f"[SECURITY] {event_type}: {details}")
        elif severity == "HIGH":
            logger.error(f"[SECURITY] {event_type}: {details}")
        elif severity == "MEDIUM":
            logger.warning(f"[SECURITY] {event_type}: {details}")
        else:
            logger.info(f"[SECURITY] {event_type}: {details}")

        # Log to audit trail
        AuditLogger.log_event(
            event_type=event_type,
            resource="security",
            status="LOGGED",
            user_id=user_id,
            details=details
        )


# ===== SINGLETON INSTANCE =====
security_middleware = SecurityMiddleware()
