"""
BookVerse Inventory Service - Demo Version
FastAPI application optimized for JFrog AppTrust demo showcase.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .api import router
from .database import initialize_database
from .config import SERVICE_NAME, SERVICE_VERSION, SERVICE_DESCRIPTION

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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


# Create FastAPI application
app = FastAPI(
    title=SERVICE_NAME,
    version=SERVICE_VERSION,
    description=SERVICE_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware for web frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory for serving book cover images
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"Mounted static files from {static_dir}")

# Include API routes
app.include_router(router)

# Legacy compatibility endpoint
@app.get("/info")
def info():
    """Legacy info endpoint for compatibility"""
    return {
        "service": "inventory",
        "version": SERVICE_VERSION,
        "name": SERVICE_NAME
    }


def main():
    """Main entry point for the package script"""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()


