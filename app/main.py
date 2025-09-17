"""
BookVerse Inventory Service - Demo Version
FastAPI application optimized for JFrog AppTrust demo showcase.

MIGRATION SUCCESS: Now using bookverse-core app factory for standardized FastAPI setup!

Benefits of this migration:
✅ Standardized middleware stack (CORS, auth, logging, error handling, request ID)
✅ Kubernetes-ready health endpoints (/health/live, /health/ready)
✅ Consistent error handling and logging across all services
✅ Built-in authentication middleware integration
✅ Standardized /info endpoint with service metadata
"""

import os
import hashlib
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Import bookverse-core app factory, configuration, logging, middleware, and health
from bookverse_core.api.app_factory import create_app
from bookverse_core.api.middleware import RequestIDMiddleware, LoggingMiddleware
from bookverse_core.api.health import create_health_router
from bookverse_core.config import BaseConfig
from bookverse_core.utils.logging import (
    setup_logging,
    LogConfig,
    get_logger,
    log_service_startup
)

from .api import router
from .database import initialize_database
from .config import SERVICE_NAME, SERVICE_VERSION, SERVICE_DESCRIPTION

# Setup standardized logging first
log_config = LogConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    include_request_id=True
)
setup_logging(log_config, "inventory")

# Get logger for this module
logger = get_logger(__name__)

# Create configuration instance
config = BaseConfig(
    service_name="inventory",
    environment=os.getenv("ENVIRONMENT", "development"),
    auth_enabled=os.getenv("AUTH_ENABLED", "true").lower() == "true",
)

# Log service startup
service_version = os.getenv("SERVICE_VERSION", SERVICE_VERSION)
log_service_startup(logger, "BookVerse Inventory Service", service_version)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - handles startup and shutdown"""
    # Startup
    logger.info("Starting BookVerse Inventory Service...")
    await initialize_database()
    logger.info("Service startup completed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down BookVerse Inventory Service...")


# Create FastAPI app using bookverse-core factory
app = create_app(
    title=SERVICE_NAME,
    version=service_version,
    description=SERVICE_DESCRIPTION,
    config=config,
    enable_auth=config.auth_enabled,
    enable_cors=True,
    health_checks=["basic", "auth"],  # Enable basic and auth health checks
    lifespan=lifespan,
    middleware_config={
        "cors": {
            "allow_origins": ["*"],  # In production, specify actual origins
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        },
        "logging": {
            "log_request_body": False,  # Don't log request bodies for performance
            "log_response_body": False,  # Don't log response bodies for performance
        },
        "request_id": {
            "header_name": "X-Request-ID",  # Standard request ID header
            "generate_if_missing": True,    # Auto-generate if not provided
        },
        "request_logging": {
            "enabled": True,                # Enable request/response logging
            "log_level": "INFO",           # Log level for requests
            "include_headers": False,       # Don't log headers for security
        }
    }
)

# Add bookverse-core middleware for enhanced request tracing and logging
app.add_middleware(RequestIDMiddleware, header_name="X-Request-ID")
app.add_middleware(LoggingMiddleware, 
                  log_requests=True,
                  log_responses=True,
                  log_request_body=False,
                  log_response_body=False)

logger.info("✅ Enhanced middleware added: Request ID tracking and request logging")

# Mount static files directory for serving book cover images
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"Mounted static files from {static_dir}")

# Include API routes
app.include_router(router)

# Add custom /info endpoint with inventory-specific metadata (override the default one)
@app.get("/info")
def get_inventory_info():
    """
    Enhanced service information endpoint with inventory-specific details.
    
    This extends the standard bookverse-core /info endpoint with service-specific metadata.
    """
    # Get base service info
    base_info = {
        "service": "inventory",
        "version": service_version,
        "name": SERVICE_NAME,
        "description": SERVICE_DESCRIPTION,
        "environment": config.environment,
        "auth_enabled": config.auth_enabled,
    }
    
    # Add inventory-specific metadata
    image_tag = os.getenv("IMAGE_TAG", os.getenv("GIT_SHA", "unknown"))
    app_version = os.getenv("APP_VERSION", "unknown")
    
    # Check static files availability
    static_available = os.path.exists(static_dir)
    static_count = 0
    if static_available:
        try:
            static_count = len([f for f in os.listdir(static_dir) if os.path.isfile(os.path.join(static_dir, f))])
        except Exception:
            static_count = 0
    
    # Combine base info with service-specific details
    base_info.update({
        "build": {"imageTag": image_tag, "appVersion": app_version},
        "config": {
            "validation": "pydantic",
            "environment_overrides": "AUTH_ENABLED, LOG_LEVEL supported"
        },
        "static_files": {
            "path": static_dir,
            "available": static_available,
            "count": static_count
        },
        "middleware": {
            "cors_enabled": True,
            "auth_enabled": config.auth_enabled,
            "logging_enabled": True,
            "error_handling_enabled": True,
            "request_id_enabled": True,
        }
    })
    
    return base_info

# Add standardized health check router (bookverse-core) alongside existing health endpoint
health_router = create_health_router(
    service_name="BookVerse Inventory Service",
    service_version=service_version,
    health_checks=["basic", "auth"]  # Match the health checks from create_app
)
app.include_router(health_router, prefix="/health", tags=["health"])

logger.info("✅ Standardized health endpoints added: /health/live, /health/ready, /health/status")

# Note: Health endpoints (/health, /health/live, /health/ready) are automatically 
# added by the bookverse-core app factory, no need to define them manually!


def main():
    """Main entry point for the package script"""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()


