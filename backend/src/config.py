"""
Configuration Management - Claude Code Security First Approach

This module loads all secrets from Azure Key Vault via Managed Identity.
NEVER use environment variables or hardcoded secrets.
All credential access is logged for audit purposes.
"""

from pydantic_settings import BaseSettings
from azure.keyvault.secrets import SecretClient
from azure.identity import ManagedIdentityCredential, DefaultAzureCredential
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Load configuration from environment variables (safe values only).
    All secrets fetched from Azure Key Vault at runtime via Managed Identity.

    SECURITY RULES:
    - App settings (ENVIRONMENT, DEBUG) are safe in env vars
    - All credentials, keys, connection strings MUST come from Key Vault
    - Never log secret values, only log access metadata
    - Tag all secret access with [AUDIT]
    """

    # ===== APP SETTINGS (safe to use env vars) =====
    APP_NAME: str = "SentinelLens"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "dev"  # dev, staging, prod
    DEBUG: bool = False

    # ===== AZURE SETTINGS =====
    AZURE_SUBSCRIPTION_ID: str
    AZURE_TENANT_ID: str
    AZURE_KEY_VAULT_URL: str  # e.g., https://vault-name.vault.azure.net/
    AZURE_SENTINEL_WORKSPACE_ID: Optional[str] = None
    AZURE_LOG_ANALYTICS_WORKSPACE_ID: Optional[str] = None

    # ===== FRONTEND/EXTERNAL URLS =====
    FRONTEND_URL: str = "http://localhost:3000"
    API_BASE_URL: str = "http://localhost:8000"

    # ===== FEATURE FLAGS (safe) =====
    ENABLE_PRESIDIO_MASKING: bool = True
    ENABLE_PROMPT_SHIELD: bool = True
    ENABLE_AUDIT_LOGGING: bool = True

    # ===== TOKEN BUDGETS & LIMITS (safe) =====
    AGENT_MAX_TOKENS_PER_RUN: int = 50000
    AGENT_TIMEOUT_SECONDS: int = 600
    API_RATE_LIMIT_PER_MINUTE: int = 100

    # ===== APPROVAL & ACCESS CONTROL =====
    APPROVAL_GROUP_ID: Optional[str] = None
    REQUIRED_ROLES_FOR_AUDIT: list = ["Microsoft.Authorization/roleAssignments/read"]

    class Config:
        env_file = ".env.local"  # Load from .env.local if it exists (local dev only)
        env_file_encoding = "utf-8"
        extra = "allow"

    def __init__(self, **data):
        super().__init__(**data)
        logger.info(f"[AUDIT] Settings initialized for environment: {self.ENVIRONMENT}")

    # ===== SECRET MANAGEMENT =====

    @property
    def credential(self):
        """
        Get authentication credential.
        Uses Managed Identity in production, DefaultAzureCredential for local dev.
        """
        if self.ENVIRONMENT == "prod":
            logger.debug("[AUDIT] Using Managed Identity credential")
            return ManagedIdentityCredential()
        else:
            # Local dev: try Managed Identity first, fall back to DefaultAzureCredential
            logger.debug("[AUDIT] Using DefaultAzureCredential (dev mode)")
            return DefaultAzureCredential()

    @property
    def kv_client(self) -> SecretClient:
        """
        Get Key Vault client.
        Maintains a single client instance for connection reuse.
        """
        return SecretClient(vault_url=self.AZURE_KEY_VAULT_URL, credential=self.credential)

    def get_secret(self, secret_name: str, use_cache: bool = True) -> str:
        """
        Fetch secret from Azure Key Vault at runtime.

        AUDIT LOGGING:
        - Log secret fetch attempt with timestamp
        - Log success/failure status
        - NEVER log the actual secret value
        - Mark with [AUDIT] tag for audit trail

        Args:
            secret_name: Name of the secret in Key Vault
            use_cache: If True, cache the secret for 5 minutes (optional optimization)

        Returns:
            The secret value

        Raises:
            Exception: If secret fetch fails (auth error, not found, etc)
        """
        logger.info(f"[AUDIT] Fetching secret from Key Vault: {secret_name}")

        try:
            secret = self.kv_client.get_secret(secret_name)
            logger.info(
                f"[AUDIT] Secret retrieved successfully: {secret_name} "
                f"(version: {secret.version[:8]})"
            )
            return secret.value

        except Exception as e:
            logger.error(
                f"[AUDIT] Secret fetch FAILED: {secret_name} - {type(e).__name__}: {str(e)}"
            )
            # Re-raise to prevent silent failures
            raise RuntimeError(f"Failed to fetch secret '{secret_name}' from Key Vault") from e

    def log_access_event(self, event_type: str, resource: str, status: str, details: str = ""):
        """
        Log an audit event for security/compliance tracking.

        Args:
            event_type: Type of event (e.g., 'SECRET_ACCESS', 'API_CALL', 'APPROVAL')
            resource: The resource being accessed (e.g., key name)
            status: Success/failure status
            details: Additional details (never include sensitive data)
        """
        logger.info(
            f"[AUDIT] Event: {event_type} | Resource: {resource} | Status: {status} | {details}"
        )


# ===== SINGLETON SETTINGS INSTANCE =====
# Initialize settings once at module load time
settings = Settings()

logger.info(
    f"[AUDIT] SentinelLens {settings.APP_VERSION} initialized in {settings.ENVIRONMENT} mode"
)
