"""
SentinelLens FastAPI Application

Main entry point for the backend service.
"""

import logging
from datetime import datetime
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from src.config import settings
from src.api.routes import router
from src.utils.logging import setup_logging

# Setup logging
setup_logging(settings.ENVIRONMENT)
logger = logging.getLogger(__name__)

# ===== FASTAPI APP INITIALIZATION =====
app = FastAPI(
    title="SentinelLens",
    description="AI-Powered Microsoft Sentinel Cost Optimization Agent",
    version=settings.APP_VERSION,
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
    redoc_url="/api/v1/redoc"
)

logger.info(f"[INIT] SentinelLens {settings.APP_VERSION} - {settings.ENVIRONMENT}")

# ===== MIDDLEWARE =====

# CORS - restrict to frontend origin only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Total-Count"],
    max_age=3600
)


# ===== MIDDLEWARE HOOKS =====
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests and responses"""
    request_id = request.headers.get("X-Request-ID", str(datetime.utcnow().timestamp()))

    logger.debug(f"[HTTP] {request.method} {request.url.path}")

    response = await call_next(request)

    logger.debug(
        f"[HTTP] Response: {response.status_code} ({request.method} {request.url.path})"
    )

    return response


# ===== EXCEPTION HANDLERS =====
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    logger.warning(f"[VALIDATION] Request validation failed: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "VALIDATION_ERROR",
            "error_message": "Invalid request body",
            "details": exc.errors(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"[ERROR] Unhandled exception: {type(exc).__name__}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "error_message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ===== STARTUP & SHUTDOWN =====
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("[STARTUP] SentinelLens backend starting")
    logger.info(f"[STARTUP] Environment: {settings.ENVIRONMENT}")
    logger.info(f"[STARTUP] Frontend URL: {settings.FRONTEND_URL}")
    logger.info(f"[STARTUP] Key Vault: {settings.AZURE_KEY_VAULT_URL}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("[SHUTDOWN] SentinelLens backend shutting down")


# ===== ROUTES =====
app.include_router(router)


# ===== HEALTH ENDPOINT (at root) =====
@app.get("/health", tags=["system"])
async def health():
    """Health check - no authentication required"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat()
    }


# ===== ROOT ENDPOINT =====
@app.get("/", tags=["system"])
async def root():
    """API root - redirect to docs"""
    return {
        "service": "SentinelLens",
        "version": settings.APP_VERSION,
        "docs": "/api/v1/docs",
        "openapi": "/api/v1/openapi.json"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
