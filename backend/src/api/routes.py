"""
FastAPI Routes - SentinelLens REST API

Endpoints:
- GET  /workspaces - List accessible workspaces
- POST /audits - Start new audit job
- GET  /audits/{job_id} - Get audit job status
- GET  /audits/{job_id}/stream - SSE stream of progress
- GET  /audits/{job_id}/report - Get full report
- POST /audits/{job_id}/approve - Approve tier changes
- GET  /audits - List all audit jobs
- GET  /health - Health check
"""

import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.config import settings
from src.models.schemas import (
    StartAuditRequest, ApprovalRequest, WorkspaceInfo, AuditJobMetadata,
    Report, HealthResponse, ErrorResponse, JobStatus
)
from src.api.auth import validate_entra_token, require_approval_group, extract_user_info
from src.services.azure_api import azure_api_service
from src.security import pii_masking, prompt_shield

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["audit"])


# ===== HEALTH CHECK =====
@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["system"]
)
async def health_check():
    """Health check endpoint (no authentication required)"""
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.utcnow()
    )


# ===== WORKSPACE MANAGEMENT =====
@router.get(
    "/workspaces",
    response_model=List[WorkspaceInfo],
    summary="List accessible Sentinel workspaces",
    description="Returns all Sentinel workspaces accessible to the authenticated user"
)
async def get_workspaces(token: dict = Depends(validate_entra_token)):
    """
    List accessible Sentinel workspaces.

    Returns workspaces from subscriptions the user has access to.
    """
    try:
        user_info = extract_user_info(token)
        logger.info(f"[AUDIT] Workspace list requested by: {user_info['user_principal']}")

        # Placeholder: In production, would list actual workspaces from subscription
        # For now, return empty list - client will be configured with workspace ID
        workspaces = []

        logger.info(f"[AUDIT] Returned {len(workspaces)} workspaces")
        return workspaces

    except Exception as e:
        logger.error(f"[AUDIT] Workspace list failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list workspaces"
        )


# ===== AUDIT JOB MANAGEMENT =====
@router.post(
    "/audits",
    response_model=AuditJobMetadata,
    summary="Start a new audit job",
    description="Initiate cost optimization audit for a Sentinel workspace"
)
async def start_audit(
    request: StartAuditRequest,
    token: dict = Depends(validate_entra_token)
):
    """
    Start a new audit job.

    Validates Entra token, creates audit job, and returns job ID.
    Async job runs in background - client polls /audits/{job_id} for status.
    """
    try:
        user_info = extract_user_info(token)

        # Validate prompt shield on user inputs
        is_safe, risk_score, reason = prompt_shield.validate(request.workspace_id)
        if not is_safe:
            logger.warning(
                f"[AUDIT] Prompt injection detected in audit request: {reason}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid input detected"
            )

        logger.info(
            f"[AUDIT] Audit job started by: {user_info['user_principal']} "
            f"for workspace: {request.workspace_id}"
        )

        # Create job (in production, would create database record)
        job_id = f"job-{datetime.utcnow().timestamp()}"

        # Return job metadata
        return AuditJobMetadata(
            job_id=job_id,
            workspace_id=request.workspace_id,
            status=JobStatus.QUEUED,
            created_at=datetime.utcnow(),
            error_message=None,
            report_url=None
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[AUDIT] Audit start failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start audit job"
        )


@router.get(
    "/audits/{job_id}",
    response_model=AuditJobMetadata,
    summary="Get audit job status",
    description="Retrieve status and metadata for an audit job"
)
async def get_audit_status(
    job_id: str,
    token: dict = Depends(validate_entra_token)
):
    """Get audit job status and metadata"""
    try:
        user_info = extract_user_info(token)
        logger.info(f"[AUDIT] Status requested for job: {job_id}")

        # Placeholder: In production, would query database
        return AuditJobMetadata(
            job_id=job_id,
            workspace_id="placeholder-ws",
            status=JobStatus.RUNNING,
            created_at=datetime.utcnow(),
            error_message=None,
            report_url=None
        )

    except Exception as e:
        logger.error(f"[AUDIT] Status check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job status"
        )


@router.get(
    "/audits/{job_id}/stream",
    summary="Real-time audit progress (SSE)",
    description="Server-sent events stream of agent tool execution progress"
)
async def stream_audit_progress(
    job_id: str,
    token: dict = Depends(validate_entra_token)
):
    """
    Stream audit progress via Server-Sent Events (SSE).

    Returns real-time updates as agent executes tools and completes steps.
    """
    async def event_generator():
        try:
            logger.info(f"[AUDIT] SSE stream opened for job: {job_id}")

            # Placeholder: In production, would stream events from agent execution
            yield f"data: {{'step': 1, 'tool': 'list_tables', 'status': 'complete'}}\n\n"
            yield f"data: {{'step': 2, 'tool': 'get_ingestion_volume', 'status': 'complete'}}\n\n"
            yield f"data: {{'step': 3, 'tool': 'list_analytics_rules', 'status': 'complete'}}\n\n"

        except Exception as e:
            logger.error(f"[AUDIT] SSE stream error: {str(e)}")
            yield f"data: {{'error': '{str(e)}'}}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get(
    "/audits/{job_id}/report",
    response_model=Report,
    summary="Get full optimization report",
    description="Retrieve complete cost optimization analysis and recommendations"
)
async def get_report(
    job_id: str,
    token: dict = Depends(validate_entra_token)
):
    """Get full audit report"""
    try:
        user_info = extract_user_info(token)
        logger.info(f"[AUDIT] Report requested for job: {job_id}")

        # Placeholder: In production, would fetch from Blob Storage
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[AUDIT] Report fetch failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get report"
        )


# ===== APPROVAL GATE (HARD SEPARATION) =====
@router.post(
    "/audits/{job_id}/approve",
    summary="Approve tier changes (HARD GATE)",
    description="Execute table tier migrations - requires security group membership"
)
async def approve_migration(
    job_id: str,
    request: ApprovalRequest,
    token: dict = Depends(validate_entra_token),
    authorized: bool = Depends(require_approval_group)
):
    """
    Approve and execute tier changes.

    HARD GATE: This is a separate service path with its own authentication.
    Only users in approval security group can execute tier changes.
    All approvals logged immutably.

    Args:
        job_id: Audit job ID
        request: List of tables to migrate
        token: Validated Entra ID token
        authorized: Must be member of approval group

    Returns:
        Approval result and execution status
    """
    try:
        if not authorized:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )

        user_info = extract_user_info(token)

        logger.warning(
            f"[AUDIT] TIER CHANGE APPROVED AND EXECUTED by: {user_info['user_principal']} "
            f"job_id={job_id} tables={len(request.table_names)}"
        )

        # Placeholder: In production, would execute tier changes via API
        return {
            "status": "approved",
            "job_id": job_id,
            "tables_migrated": request.table_names,
            "executed_at": datetime.utcnow()
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[AUDIT] Approval failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Approval execution failed"
        )


# ===== AUDIT HISTORY =====
@router.get(
    "/audits",
    response_model=List[AuditJobMetadata],
    summary="List all audit jobs",
    description="Retrieve history of audit jobs with pagination"
)
async def list_audits(
    skip: int = 0,
    limit: int = 50,
    token: dict = Depends(validate_entra_token)
):
    """List all audit jobs (paginated)"""
    try:
        user_info = extract_user_info(token)
        logger.info(f"[AUDIT] Audit history requested")

        # Placeholder: In production, would query database with pagination
        return []

    except Exception as e:
        logger.error(f"[AUDIT] Audit list failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list audits"
        )


# ===== ERROR HANDLING =====
@router.get(
    "/error",
    response_model=ErrorResponse,
    tags=["system"]
)
async def error_example():
    """Example error response"""
    return ErrorResponse(
        error_code="EXAMPLE",
        error_message="This is an example error",
        timestamp=datetime.utcnow()
    )
