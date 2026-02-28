"""
Security Utilities - PII Masking & Prompt Shield Integration

This module implements two-stage security:
1. PII Masking: Detect and replace sensitive data before LLM processing
2. Prompt Shield: Detect and reject prompt injection attempts

All data flowing through the LLM pipeline is sanitized here.
"""

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
    Simple PII masking using regex patterns.

    Detects and masks:
    - Email addresses
    - IP addresses
    - URLs
    - Phone numbers
    """

    def __init__(self):
        """Initialize PII masking patterns"""
        self.patterns = {
            "EMAIL": r"[\w\.-]+@[\w\.-]+\.\w+",
            "IP_ADDRESS": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "URL": r"https?://[^\s]+",
            "PHONE": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        }
        logger.info("[SECURITY] PII Masking Pipeline initialized")

    def mask(self, text: str) -> MaskingResult:
        """
        Apply PII masking to text using regex patterns.

        Args:
            text: Input text (typically KQL, table names, metadata)

        Returns:
            MaskingResult with masked text and entity count
        """
        try:
            masked_text = text
            total_found = 0
            entities = []

            for entity_type, pattern in self.patterns.items():
                matches = list(re.finditer(pattern, text))
                if matches:
                    total_found += len(matches)
                    for i, match in enumerate(matches):
                        placeholder = f"[{entity_type}_{i}]"
                        masked_text = masked_text.replace(match.group(), placeholder)
                        entities.append({
                            "type": entity_type,
                            "start": match.start(),
                            "end": match.end(),
                        })

            if total_found > 0:
                logger.info(f"[SECURITY] Found and masked {total_found} PII entities")

            return MaskingResult(
                original_text=text,
                masked_text=masked_text,
                pii_entities_found=total_found,
                entities=entities,
            )

        except Exception as e:
            logger.error(f"[SECURITY] PII masking failed: {type(e).__name__}: {str(e)}")
            return MaskingResult(
                original_text=text,
                masked_text=text,
                pii_entities_found=0,
                entities=[],
            )


class PromptShieldValidator:
    """
    Prompt injection detection using local heuristic patterns.

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
            risk_threshold: Risk score threshold (0-1) to reject prompt

        Returns:
            (is_safe, risk_score, reason) - True if safe, False if injection detected
        """
        try:
            matches = 0
            for pattern in self.injection_patterns:
                if re.search(pattern, prompt):
                    matches += 1

            risk_score = min(1.0, matches / len(self.injection_patterns))

            if risk_score > risk_threshold:
                reason = f"Potential injection detected (score: {risk_score:.2f})"
                logger.warning(f"[SECURITY] Prompt Shield BLOCKED: {reason}")
                return False, risk_score, reason

            return True, risk_score, "Safe"

        except Exception as e:
            logger.error(f"[SECURITY] Prompt validation error: {str(e)}")
            return True, 0.0, "Error during validation"


class DataSanitizer:
    """Sanitize sensitive data from logs and responses"""

    SENSITIVE_PATTERNS = {
        "bearer_token": r"Bearer\s+[a-zA-Z0-9\._\-]+",
        "api_key": r"(api[_-]?key|apikey)\s*[=:]\s*['\"]?[a-zA-Z0-9\._\-]+['\"]?",
        "connection_string": r"(connection[_-]?string|connstr)\s*[=:]\s*[^;]+",
        "password": r"(password|passwd|pwd)\s*[=:]\s*['\"]?[^'\";]+['\"]?",
    }

    @staticmethod
    def sanitize_logs(text: str) -> str:
        """
        Sanitize logs by removing/masking sensitive values.

        Args:
            text: Log text to sanitize

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
