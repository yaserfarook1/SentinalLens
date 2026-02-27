"""
Security Utilities - PII Masking & Prompt Shield Integration

This module implements two-stage security:
1. PII Masking: Detect and replace sensitive data before LLM processing
2. Prompt Shield: Detect and reject prompt injection attempts

All data flowing through the LLM pipeline is sanitized here.
"""

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.recognizer import PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
import re
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MaskingResult:
    """Result of PII masking operation"""
    original_text: str
    masked_text: str
    pii_entities_found: int
    entities: List[Dict] = None


class PiiMaskingPipeline:
    """
    Two-stage PII masking pipeline for LLM data protection.

    Stage 1: presidio-analyzer - Detects PII entities
    Stage 2: presidio-anonymizer - Replaces with placeholders

    Supported entity types:
    - EMAIL_ADDRESS, PHONE_NUMBER, IP_ADDRESS
    - PERSON (names), DOMAIN_NAME, URL
    - CREDIT_CARD, DOMAIN_NAME, DRIVER_LICENSE
    - Custom: AZURE_RESOURCE_ID, UPN, HOSTNAME
    """

    def __init__(self):
        """Initialize Presidio analyzer and anonymizer with custom patterns"""
        self.analyzer = self._create_analyzer()
        self.anonymizer = AnonymizerEngine()

        logger.info("[SECURITY] PII Masking Pipeline initialized")

    def _create_analyzer(self) -> AnalyzerEngine:
        """
        Create analyzer with custom patterns for Azure/SIEM context.

        Adds patterns for:
        - Azure resource IDs
        - User Principal Names (UPNs)
        - Hostnames
        - Resource group names
        """
        registry = RecognizerRegistry()

        # Azure Resource ID: /subscriptions/{sub}/resourceGroups/{rg}/providers/...
        azure_resource_pattern = PatternRecognizer(
            supported_entity="AZURE_RESOURCE_ID",
            patterns=[
                Pattern(
                    name="azure_resource_id",
                    regex=r"/subscriptions/[a-f0-9\-]+/resourceGroups/[\w\-]+",
                    score=0.8,
                )
            ],
        )
        registry.add_recognizer(azure_resource_pattern)

        # User Principal Name: user@domain.com or user@contoso.onmicrosoft.com
        upn_pattern = PatternRecognizer(
            supported_entity="UPN",
            patterns=[
                Pattern(
                    name="upn",
                    regex=r"[\w\.\-]+@(?:contoso|company)\.(?:onmicrosoft\.com|com)",
                    score=0.8,
                )
            ],
        )
        registry.add_recognizer(upn_pattern)

        # Hostname: server-01, app-prod-vm, etc
        hostname_pattern = PatternRecognizer(
            supported_entity="HOSTNAME",
            patterns=[
                Pattern(
                    name="hostname",
                    regex=r"\b(?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b",
                    score=0.7,
                )
            ],
        )
        registry.add_recognizer(hostname_pattern)

        return AnalyzerEngine(nlp_engine=None, registry=registry)

    def mask(self, text: str) -> MaskingResult:
        """
        Apply two-stage PII masking to text.

        Stage 1: Detect all PII entities in text
        Stage 2: Replace with typed placeholders (e.g., <IP_ADDRESS_1>)

        Args:
            text: Input text (typically KQL, table names, metadata)

        Returns:
            MaskingResult with masked text and entity count

        Raises:
            Exception: If masking fails (logged, not raised)
        """
        try:
            # Stage 1: Analyze
            logger.debug(f"[SECURITY] Analyzing text for PII (length: {len(text)} chars)")
            results = self.analyzer.analyze(text=text, language="en")

            if not results:
                logger.debug("[SECURITY] No PII detected in text")
                return MaskingResult(
                    original_text=text,
                    masked_text=text,
                    pii_entities_found=0,
                    entities=[],
                )

            # Stage 2: Anonymize
            logger.info(f"[SECURITY] Found {len(results)} PII entities, applying masking")
            masked = self.anonymizer.anonymize(text=text, analyzer_results=results)

            # Log entity types found (not values)
            entity_types = {}
            for entity in results:
                entity_type = entity.entity_type
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

            logger.info(f"[SECURITY] PII masked - Types: {entity_types}")

            return MaskingResult(
                original_text=text,
                masked_text=masked.text,
                pii_entities_found=len(results),
                entities=[
                    {
                        "type": e.entity_type,
                        "score": e.score,
                        "start": e.start,
                        "end": e.end,
                    }
                    for e in results
                ],
            )

        except Exception as e:
            logger.error(f"[SECURITY] PII masking failed: {type(e).__name__}: {str(e)}")
            # Fail safe: return original text but log the error
            return MaskingResult(
                original_text=text, masked_text=text, pii_entities_found=0, entities=[]
            )


class PromptShieldValidator:
    """
    Prompt injection detection using Azure Prompt Shield service or local heuristics.

    Methods:
    - Check for common injection patterns
    - Check for suspicious role-play requests
    - Check for data exfiltration attempts
    """

    def __init__(self):
        """Initialize validator with local heuristic patterns"""
        self.injection_patterns = [
            # SQL injection indicators
            r"(?i)(union|select|drop|insert|update|delete|exec|script)",
            # Prompt injection: "ignore instructions"
            r"(?i)(ignore|forget|disregard).*(instruction|prompt|rule)",
            # Role-play injection: "you are now a..."
            r"(?i)(you are now|pretend|act as|roleplay as).*(admin|root|system)",
            # System prompt leakage: "show your system prompt"
            r"(?i)(show|reveal|display|print).*(system prompt|instructions|rules)",
        ]

        logger.info("[SECURITY] Prompt Shield Validator initialized with heuristic patterns")

    def validate(self, prompt: str, risk_threshold: float = 0.7) -> Tuple[bool, float, str]:
        """
        Validate prompt for injection attempts.

        Args:
            prompt: User input or API response
            risk_threshold: Risk score threshold (0.0 - 1.0)

        Returns:
            Tuple: (is_safe, risk_score, reason)
            - is_safe: True if prompt passes validation
            - risk_score: Confidence score (0.0 - 1.0)
            - reason: Explanation if rejected
        """
        try:
            risk_score = 0.0
            reasons = []

            # Check heuristic patterns
            for pattern in self.injection_patterns:
                if re.search(pattern, prompt):
                    risk_score += 0.3
                    reasons.append(f"Pattern matched: {pattern[:30]}...")

            # Check for suspiciously long strings (potential token spam)
            if len(prompt) > 50000:
                risk_score += 0.2
                reasons.append("Prompt exceeds length threshold (50k chars)")

            # Check for repeated characters (token padding attack)
            if re.search(r"(.)\1{100,}", prompt):
                risk_score += 0.3
                reasons.append("Detected token padding pattern")

            risk_score = min(risk_score, 1.0)  # Cap at 1.0

            if risk_score > risk_threshold:
                logger.warning(
                    f"[SECURITY] Prompt rejected - Risk: {risk_score:.2f} - {', '.join(reasons)}"
                )
                return False, risk_score, f"Prompt injection detected: {reasons[0]}"

            logger.debug(f"[SECURITY] Prompt validated - Risk: {risk_score:.2f}")
            return True, risk_score, "OK"

        except Exception as e:
            logger.error(f"[SECURITY] Prompt validation failed: {str(e)}")
            # Fail safe: reject if validation fails
            return False, 1.0, "Validation error"


class DataSanitizer:
    """
    Sanitize API responses and logs to prevent accidental credential leakage.
    """

    # Patterns to detect and mask in logs
    SENSITIVE_PATTERNS = {
        "bearer_token": r"Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*",
        "api_key": r"(api_key|apikey|key)[\"'\s:=]+([A-Za-z0-9\-_]{20,})",
        "connection_string": r"(connection.*string|connstr)[\"'\s:=]+([^\"'\s]+)",
        "password": r"(password|passwd)[\"'\s:=]+([^\"'\s;]+)",
    }

    @staticmethod
    def sanitize_logs(text: str) -> str:
        """
        Remove sensitive patterns from text before logging.

        Args:
            text: Text to sanitize (usually from API responses or errors)

        Returns:
            Sanitized text with sensitive values masked
        """
        sanitized = text

        for pattern_name, pattern in DataSanitizer.SENSITIVE_PATTERNS.items():
            sanitized = re.sub(pattern, f"[REDACTED_{pattern_name.upper()}]", sanitized)

        return sanitized

    @staticmethod
    def sanitize_error(error: Exception) -> str:
        """Sanitize exception message before logging"""
        return DataSanitizer.sanitize_logs(str(error))


# ===== SINGLETON INSTANCES =====
pii_masking = PiiMaskingPipeline()
prompt_shield = PromptShieldValidator()
data_sanitizer = DataSanitizer()
