"""
Configuration for BookVerse Inventory Service - Demo Version
Simple hardcoded values optimized for AppTrust demo showcase.
"""

import os
from pathlib import Path

# Database Configuration (SQLite for simplicity)
DATABASE_URL = "sqlite:///./bookverse_inventory.db"

# Demo Configuration
LOG_LEVEL = "INFO"

# Paths
APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
DEMO_BOOKS_FILE = DATA_DIR / "demo_books.json"
DEMO_INVENTORY_FILE = DATA_DIR / "demo_inventory.json"

# API Configuration
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# Service Information
SERVICE_NAME = "BookVerse Inventory Service"
SERVICE_VERSION = "1.0.0-demo"
SERVICE_DESCRIPTION = "Demo inventory service showcasing JFrog AppTrust capabilities"

# Demo Settings
LOW_STOCK_THRESHOLD = 5
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
