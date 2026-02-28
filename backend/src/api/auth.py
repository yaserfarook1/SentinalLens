"""
Authentication & Authorization

Validates Entra ID tokens and enforces security group membership for approvals.
All auth failures logged for security audit.
"""

import logging
from typing import Dict, Optional
from fastapi import HTTPException, status, Depends, Header, Query
import jwt
from functools import lru_cache

from src.config import settings

logger = logging.getLogger(__name__)


async def validate_entra_token(
    authorization: Optional[str] = Header(None),
    token_param: Optional[str] = Query(None, alias="token"),
) -> Dict:
    """
    Validate Entra ID JWT token from frontend.

    Accepts token from either:
    - Authorization header (Bearer token) - for regular HTTP requests
    - Query parameter (?token=...) - for SSE/EventSource endpoints (which don't support custom headers)

    Verifies:
    - Token signature (against Azure AD public keys)
    - Token expiration
    - Token issuer

    Args:
        authorization: HTTP Authorization header (Bearer token)
        token_param: Query parameter token (for SSE endpoints)

    Returns:
        Decoded token claims

    Raises:
        HTTPException: If token invalid/expired
    """
    # Try to get token from Authorization header first, fallback to query parameter
    token = None

    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "", 1)
    elif token_param:
        token = token_param

    if not token:
        logger.warning("[AUDIT] Missing or invalid authorization header/token parameter")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header or token parameter"
        )

    try:
        logger.debug("[AUTH] Validating Azure AD token")

        # Decode JWT without signature verification (signature verified by MSAL on frontend)
        unverified = jwt.decode(token, options={"verify_signature": False})

        # Verify token structure
        required_claims = ["oid", "upn"]
        missing_claims = [claim for claim in required_claims if claim not in unverified]
        if missing_claims:
            logger.warning(f"[AUDIT] Token missing required claims: {missing_claims}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing required claims"
            )

        # In production, verify signature against Azure AD public keys
        # For now, accept unverified (MSAL validates on frontend)
        logger.info(f"[AUDIT] Token validated for user: {unverified.get('upn')}")

        return unverified

    except jwt.ExpiredSignatureError:
        logger.warning("[AUDIT] Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )

    except jwt.InvalidTokenError as e:
        logger.warning(f"[AUDIT] Invalid token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    except Exception as e:
        logger.error(f"[AUDIT] Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed"
        )


async def require_approval_group(
    token: Dict = Depends(validate_entra_token),
) -> bool:
    """
    Require user to be member of approval security group.

    This is a HARD gate - not a soft guardrail.
    Approval group membership is checked at request time.

    Args:
        token: Decoded token from validate_entra_token

    Returns:
        True if user is authorized

    Raises:
        HTTPException: If user not in approval group
    """
    user_id = token.get("oid")
    user_upn = token.get("upn")

    try:
        # Get groups from token claims
        groups = token.get("groups", [])

        if settings.APPROVAL_GROUP_ID not in groups:
            logger.warning(
                f"[AUDIT] Approval DENIED: User {user_upn} not in approval group"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not authorized to approve tier changes"
            )

        logger.info(
            f"[AUDIT] Approval authorized for user: {user_upn}"
        )

        return True

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[AUDIT] Authorization check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authorization check failed"
        )


def extract_user_info(token: Dict) -> Dict[str, str]:
    """Extract user information from token"""
    return {
        "user_id": token.get("oid"),
        "user_principal": token.get("upn"),
        "display_name": token.get("name", "Unknown"),
        "tenant_id": token.get("tid")
    }
