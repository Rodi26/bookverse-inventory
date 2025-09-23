



import logging
import time
from typing import Dict, Any, List, Optional, Callable

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import check_auth_connection, get_auth_status
from .responses import HealthResponse, create_health_response

logger = logging.getLogger(__name__)

_service_start_time = time.time()


def create_health_router(
    service_name: str = "BookVerse Service",
    service_version: str = "1.0.0",
    health_checks: Optional[List[str]] = None
) -> APIRouter:
    
        
    router = APIRouter(tags=["health"])
    health_checks = health_checks or ["basic"]
    
    @router.get("/health", response_model=HealthResponse)
    async def health_check():
        
        checks = {}
        overall_status = "healthy"
        
        for check_type in health_checks:
            try:
                if check_type == "basic":
                    checks["basic"] = {"status": "healthy", "message": "Service is running"}
                elif check_type == "auth":
                    auth_status = await check_auth_connection()
                    checks["auth"] = auth_status
                    if auth_status.get("status") != "healthy":
                        overall_status = "degraded"
                elif check_type == "database":
                    checks["database"] = {"status": "not_implemented", "message": "Database check not implemented"}
                else:
                    checks[check_type] = {"status": "unknown", "message": f"Unknown check type: {check_type}"}
            except Exception as e:
                logger.error(f"Health check failed for {check_type}: {e}")
                checks[check_type] = {"status": "unhealthy", "error": str(e)}
                overall_status = "unhealthy"
        
        uptime = time.time() - _service_start_time
        
        return create_health_response(
            status=overall_status,
            service=service_name,
            version=service_version,
            checks=checks,
            uptime=uptime
        )
    
    @router.get("/health/live")
    async def liveness_check():
        
        return {"status": "alive", "timestamp": time.time()}
    
    @router.get("/health/ready")
    async def readiness_check():
        
        try:
            return {"status": "ready", "timestamp": time.time()}
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            raise HTTPException(status_code=503, detail="Service not ready")
    
    @router.get("/health/auth")
    async def auth_health_check():
        
        if "auth" not in health_checks:
            raise HTTPException(status_code=404, detail="Auth health check not enabled")
        
        try:
            auth_status = get_auth_status()
            auth_connection = await check_auth_connection()
            
            return {
                "auth_config": auth_status,
                "auth_connection": auth_connection,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"Auth health check failed: {e}")
            raise HTTPException(status_code=503, detail=f"Auth health check failed: {str(e)}")
    
    return router


def create_database_health_check(get_db: Callable[[], Session]):
    
        
    async def check_database_health(db: Session = Depends(get_db)) -> Dict[str, Any]:
        try:
            from sqlalchemy import text
            result = db.execute(text("SELECT 1"))
            result.fetchone()
            
            return {
                "status": "healthy",
                "message": "Database connection successful",
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
    
    return check_database_health


def create_custom_health_check(
    name: str,
    check_function: Callable[[], Dict[str, Any]]
):
    
        
    async def custom_health_check():
        try:
            result = await check_function() if callable(check_function) else check_function()
            return {
                "check": name,
                "result": result,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"Custom health check '{name}' failed: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Health check '{name}' failed: {str(e)}"
            )
    
    return custom_health_check


def get_service_uptime() -> float:
    
    return time.time() - _service_start_time


def reset_service_start_time():
    
    global _service_start_time
    _service_start_time = time.time()


