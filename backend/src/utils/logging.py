"""
Logging Configuration & Utilities

Sets up logging for audit trail, error tracking, and monitoring.
All sensitive data is sanitized before logging.
"""

import logging
import logging.handlers
import sys
from typing import Optional


def setup_logging(environment: str, level: str = "INFO"):
    """
    Configure logging for the application.

    Args:
        environment: dev, staging, prod
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level))

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level))

    # Format with timestamp, level, module, message
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler for production (optional)
    if environment == "prod":
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                filename="sentinellens.log",
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5
            )
            file_handler.setLevel(logging.WARNING)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"Failed to setup file logging: {str(e)}")


def get_logger(module_name: str) -> logging.Logger:
    """Get a logger for a module"""
    return logging.getLogger(module_name)


class AuditLogger:
    """Dedicated logger for audit trail events"""

    @staticmethod
    def log_event(
        event_type: str,
        resource: str,
        status: str,
        user_id: Optional[str] = None,
        details: str = ""
    ):
        """
        Log an audit event.

        Args:
            event_type: Type of event (e.g., SECRET_ACCESS, APPROVAL_EXECUTED)
            resource: Resource being accessed
            status: SUCCESS or FAILURE
            user_id: Entra ID user ID
            details: Additional details (never include sensitive data)
        """
        logger = logging.getLogger("audit")

        message = (
            f"[AUDIT] "
            f"event={event_type} | "
            f"resource={resource} | "
            f"status={status}"
        )

        if user_id:
            message += f" | user={user_id}"

        if details:
            message += f" | {details}"

        if status == "FAILURE":
            logger.error(message)
        else:
            logger.info(message)

    @staticmethod
    def log_secret_access(secret_name: str, status: str):
        """Log secret access from Key Vault"""
        AuditLogger.log_event(
            event_type="SECRET_ACCESS",
            resource=secret_name,
            status=status
        )

    @staticmethod
    def log_approval(job_id: str, tables: int, user_id: str):
        """Log approval execution"""
        AuditLogger.log_event(
            event_type="APPROVAL_EXECUTED",
            resource=job_id,
            status="SUCCESS",
            user_id=user_id,
            details=f"tables_migrated={tables}"
        )

    @staticmethod
    def log_tool_execution(tool_name: str, status: str, result_count: int = 0):
        """Log agent tool execution"""
        AuditLogger.log_event(
            event_type="TOOL_EXECUTED",
            resource=tool_name,
            status=status,
            details=f"results={result_count}"
        )
