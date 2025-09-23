

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from ..auth import JWTAuthMiddleware
from ..config import BaseConfig
from .middleware import LoggingMiddleware, RequestIDMiddleware, ErrorHandlingMiddleware
from .health import create_health_router

logger = logging.getLogger(__name__)


def create_app(
    title: str = "BookVerse Service",
    version: str = "1.0.0",
    description: str = "A BookVerse microservice",
    config: Optional[BaseConfig] = None,
    enable_auth: bool = True,
    enable_cors: bool = True,
    enable_static_files: bool = False,
    static_directory: Optional[str] = None,
    health_checks: Optional[List[str]] = None,
    middleware_config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> FastAPI:
    
        
    app_kwargs = {
        "title": title,
        "version": version,
        "description": description,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": "/openapi.json",
    }
    
    app_kwargs.update(kwargs)
    
    app = FastAPI(**app_kwargs)
    
    app.add_middleware(RequestIDMiddleware)
    
    app.add_middleware(ErrorHandlingMiddleware)
    
    logging_config = middleware_config.get("logging", {}) if middleware_config else {}
    app.add_middleware(LoggingMiddleware, **logging_config)
    
    if enable_cors:
        cors_config = middleware_config.get("cors", {}) if middleware_config else {}
        cors_defaults = {
            "allow_origins": ["*"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }
        cors_defaults.update(cors_config)
        
        app.add_middleware(CORSMiddleware, **cors_defaults)
        logger.info("✅ CORS middleware enabled")
    
    if enable_auth:
        auth_config = middleware_config.get("auth", {}) if middleware_config else {}
        app.add_middleware(JWTAuthMiddleware, **auth_config)
        logger.info("✅ JWT authentication middleware enabled")
    
    if enable_static_files:
        static_dir = static_directory or "static"
        static_path = Path(static_dir)
        
        if static_path.exists():
            app.mount("/static", StaticFiles(directory=static_dir), name="static")
            logger.info(f"✅ Static files mounted from {static_dir}")
        else:
            logger.warning(f"⚠️ Static directory not found: {static_dir}")
    
    health_router = create_health_router(
        service_name=title,
        service_version=version,
        health_checks=health_checks or []
    )
    app.include_router(health_router)
    
    @app.get("/info")
    def get_service_info():
        info = {
            "service": title,
            "version": version,
            "description": description,
        }
        
        if config:
            info.update({
                "environment": config.environment,
                "api_version": config.api_version,
                "auth_enabled": config.auth_enabled,
            })
        
        return info
    
    logger.info(f"🚀 Starting {title} v{version}")
    if config:
        logger.info(f"📋 Environment: {config.environment}")
        logger.info(f"🔐 Auth enabled: {config.auth_enabled}")
    
    
    logger.info(f"✅ FastAPI application created: {title} v{version}")
    return app


def create_minimal_app(
    title: str = "BookVerse Service",
    version: str = "1.0.0",
    **kwargs
) -> FastAPI:
    
    
        
    return create_app(
        title=title,
        version=version,
        enable_auth=False,
        enable_cors=True,
        enable_static_files=False,
        health_checks=["basic"],
        **kwargs
    )


def add_custom_middleware(app: FastAPI, middleware_class, **kwargs):
    
    app.add_middleware(middleware_class, **kwargs)
    logger.info(f"✅ Added custom middleware: {middleware_class.__name__}")


def configure_static_files(app: FastAPI, directory: str, mount_path: str = "/static"):
    
    static_path = Path(directory)
    if static_path.exists():
        app.mount(mount_path, StaticFiles(directory=directory), name="static")
        logger.info(f"✅ Static files configured: {directory} -> {mount_path}")
    else:
        logger.error(f"❌ Static directory not found: {directory}")
        raise FileNotFoundError(f"Static directory not found: {directory}")
