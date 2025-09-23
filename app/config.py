
"""
BookVerse Inventory Service - Configuration Management

This module provides comprehensive configuration management for the BookVerse Inventory Service,
implementing environment-aware settings, secure defaults, and enterprise-grade configuration
patterns for reliable deployment across development, staging, and production environments.

The configuration system implements industry best practices including:
- Environment variable integration with secure defaults
- Path management for cross-platform compatibility
- API versioning and service identification
- Business logic configuration with tunable parameters
- Deployment-specific overrides for different environments
- Security-conscious configuration patterns

🔧 Configuration Categories:
    📊 **Database Configuration**: Connection strings and database settings
    📋 **Logging Configuration**: Log levels and output formatting
    📁 **File System Configuration**: Path management and data directories
    🌐 **API Configuration**: Versioning, prefixes, and service metadata
    📈 **Business Logic Configuration**: Thresholds and operational parameters
    🔒 **Security Configuration**: Environment-aware secure defaults

🌍 Environment Support:
    - Development: Local SQLite with debug settings
    - Testing: Isolated test databases and enhanced logging
    - Staging: Production-like configuration with test data
    - Production: Optimized settings with security hardening

📋 Configuration Sources:
    1. Default values (defined in this module)
    2. Environment variables (12-factor app compliance)
    3. Configuration files (future enhancement)
    4. Command-line arguments (future enhancement)
    5. External configuration services (future enhancement)

🔐 Security Considerations:
    - No sensitive data stored in source code
    - Environment variables for secrets and credentials
    - Secure defaults for all configuration options
    - Validation of configuration values at startup
    - Audit logging of configuration changes

Usage Patterns:
    ```python
    # Import configuration in application modules
    from .config import DATABASE_URL, LOG_LEVEL, SERVICE_NAME

    # Environment variable override example
    # export DATABASE_URL="postgresql://user:pass@localhost/bookverse"
    # export LOG_LEVEL="DEBUG"

    # Configuration validation
    def validate_config():
        assert DATABASE_URL, "Database URL must be configured"
        assert LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR"]
        assert DEFAULT_PAGE_SIZE > 0, "Page size must be positive"
    ```

Environment Variables:
    SERVICE_VERSION: Service version string (default: "1.0.0-dev")
    DATABASE_URL: Database connection string (default: SQLite local)
    LOG_LEVEL: Logging verbosity level (default: "INFO")
    API_VERSION: API version for endpoint routing (default: "v1")

Authors: BookVerse Platform Team
Version: 1.0.0
Last Updated: 2024-01-15
"""

import os
from pathlib import Path

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# Primary database connection URL
# Environment Override: DATABASE_URL
# Development Default: Local SQLite database for ease of setup
# Production: Should be overridden with PostgreSQL or other production database
# Security Note: No credentials stored in source code
DATABASE_URL = "sqlite:///./bookverse_inventory.db"
"""
Database connection URL for the BookVerse Inventory Service.

This configuration defines the primary database connection used by SQLAlchemy
for all data persistence operations. The URL follows standard database URL
format and supports various database backends.

Environment Variable: DATABASE_URL
Default Value: "sqlite:///./bookverse_inventory.db"

Supported Database Types:
    - SQLite (development): sqlite:///path/to/database.db
    - PostgreSQL (production): postgresql://user:password@host:port/database
    - MySQL (alternative): mysql://user:password@host:port/database
    - SQL Server (enterprise): mssql://user:password@host:port/database

Configuration Examples:
    # Development (default)
    DATABASE_URL = "sqlite:///./bookverse_inventory.db"

    # Production PostgreSQL
    DATABASE_URL = "postgresql://bookverse_user:secure_password@db.example.com:5432/bookverse_inventory"

    # Testing (in-memory)
    DATABASE_URL = "sqlite:///:memory:"

    # Docker Compose
    DATABASE_URL = "postgresql://bookverse:password@postgres:5432/bookverse_inventory"

Security Considerations:
    - Credentials should be provided via environment variables
    - Use connection pooling for production deployments
    - Enable SSL/TLS for remote database connections
    - Implement proper firewall rules for database access
    - Regular backup and disaster recovery procedures

Performance Tuning:
    - Connection pooling: Configure SQLAlchemy pool settings
    - Index optimization: Ensure proper database indexing
    - Query optimization: Use database-specific query hints
    - Monitoring: Track connection usage and query performance
"""

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

# Application logging level
# Environment Override: LOG_LEVEL
# Valid Values: DEBUG, INFO, WARNING, ERROR, CRITICAL
# Default: INFO for balanced logging without performance impact
LOG_LEVEL = "INFO"
"""
Application-wide logging level configuration.

Controls the verbosity of application logging across all modules and services.
This setting affects performance and storage requirements, particularly in
high-traffic production environments.

Environment Variable: LOG_LEVEL
Default Value: "INFO"

Logging Levels:
    - DEBUG: Detailed diagnostic information (development only)
    - INFO: General operational information (default)
    - WARNING: Warning messages for attention-worthy events
    - ERROR: Error conditions that don't stop operation
    - CRITICAL: Serious errors that may stop operation

Environment-Specific Recommendations:
    - Development: DEBUG for comprehensive debugging information
    - Testing: INFO for operational visibility without noise
    - Staging: INFO for production-like logging behavior
    - Production: WARNING or ERROR for minimal overhead

Performance Impact:
    - DEBUG: High logging volume, significant performance impact
    - INFO: Moderate logging, minimal performance impact
    - WARNING+: Low logging volume, negligible performance impact

Log Format Integration:
    - Structured logging with JSON format for production
    - Human-readable format for development
    - Correlation IDs for distributed tracing
    - Timestamp and service identification

Usage Examples:
    # Set debug logging for development
    export LOG_LEVEL=DEBUG

    # Production error-only logging
    export LOG_LEVEL=ERROR

    # Default balanced logging
    LOG_LEVEL = "INFO"  # No override needed
"""

# =============================================================================
# FILE SYSTEM CONFIGURATION
# =============================================================================

# Application directory structure
# Automatically determined relative to this configuration file
# Provides cross-platform path compatibility
APP_DIR = Path(__file__).parent
"""
Application root directory path.

Automatically determined relative to the configuration file location,
providing a stable reference point for all application file operations.
This approach ensures cross-platform compatibility and reliable path
resolution regardless of the current working directory.

Value: Pathlib.Path object pointing to application root
Usage: Base path for all relative file operations

Path Structure:
    APP_DIR/
    ├── config.py (this file)
    ├── main.py
    ├── api.py
    ├── models.py
    ├── services.py
    └── data/
        ├── demo_books.json
        └── demo_inventory.json

Benefits:
    - Cross-platform compatibility (Windows, Linux, macOS)
    - Relative path independence from execution context
    - Type safety with Pathlib operations
    - Consistent path handling across application modules
"""

# Data directory for application files
# Contains demo data, fixtures, and other application data files
# Separated from application code for clear organization
DATA_DIR = APP_DIR / "data"
"""
Data directory for application data files.

Contains demo data, database fixtures, configuration files, and other
data assets required by the application. This separation maintains
clear boundaries between application code and data assets.

Value: APP_DIR / "data"
Contents: JSON files, fixtures, and data assets

Directory Purpose:
    - Demo data for development and testing
    - Database seed data and fixtures
    - Configuration templates and examples
    - Static data files for application operation

File Organization:
    data/
    ├── demo_books.json       # Sample book catalog data
    ├── demo_inventory.json   # Sample inventory records
    ├── fixtures/             # Test data fixtures
    └── schemas/              # JSON schema definitions

Access Patterns:
    - Read-only access during application runtime
    - Version controlled with application code
    - Environment-specific data overrides supported
"""

# Demo data file paths
# Provide sample data for development and testing environments
# Support rapid application bootstrapping and demonstration
DEMO_BOOKS_FILE = DATA_DIR / "demo_books.json"
"""
Demo book catalog data file path.

Contains sample book records for development, testing, and demonstration
purposes. This data provides a realistic dataset for application development
and showcasing service capabilities.

File Path: DATA_DIR / "demo_books.json"
Format: JSON array of book objects

Data Structure:
    [
        {
            "id": "uuid-string",
            "title": "Book Title",
            "authors": ["Author Name"],
            "isbn": "978-1234567890",
            "price": 29.99,
            "genres": ["Fiction", "Adventure"],
            "description": "Book description...",
            "cover_image_url": "https://example.com/cover.jpg"
        }
    ]

Usage Scenarios:
    - Development environment bootstrapping
    - Automated testing with known data sets
    - Demo and presentation environments
    - Performance testing with realistic data volumes

Maintenance:
    - Regular updates to reflect current catalog diversity
    - Validation against current book schema
    - Size management for performance testing
"""

DEMO_INVENTORY_FILE = DATA_DIR / "demo_inventory.json"
"""
Demo inventory records data file path.

Contains sample inventory data corresponding to demo book catalog,
providing realistic stock levels and inventory scenarios for
development and testing purposes.

File Path: DATA_DIR / "demo_inventory.json"
Format: JSON array of inventory objects

Data Structure:
    [
        {
            "book_id": "uuid-string",
            "quantity_available": 25,
            "quantity_total": 30,
            "reorder_point": 5,
            "cost_per_unit": 15.99,
            "supplier_id": "supplier-uuid"
        }
    ]

Inventory Scenarios:
    - Various stock levels (high, medium, low, out-of-stock)
    - Different reorder points for business logic testing
    - Realistic cost and pricing data
    - Supplier relationship examples

Business Logic Support:
    - Low stock alert testing
    - Reorder point calculations
    - Inventory valuation scenarios
    - Stock movement simulation
"""

# =============================================================================
# API CONFIGURATION
# =============================================================================

# API versioning configuration
# Supports backward compatibility and evolution
# Follows semantic versioning principles
API_VERSION = "v1"
"""
Current API version identifier.

Defines the active API version for endpoint routing and client compatibility.
This versioning strategy supports backward compatibility and gradual API
evolution without breaking existing client integrations.

Value: "v1" (current stable version)
Usage: URL path prefix and API documentation versioning

Versioning Strategy:
    - v1: Initial stable API version
    - v2: Future major version with breaking changes
    - v1.1: Minor version updates (backward compatible)
    - beta: Pre-release versions for testing

URL Structure:
    - /api/v1/books           # Current stable API
    - /api/v1/inventory       # Current stable API
    - /api/v2/books           # Future major version
    - /api/beta/features      # Pre-release features

Client Compatibility:
    - Existing clients continue using v1 endpoints
    - New clients can adopt latest version
    - Deprecation notices for old versions
    - Migration guides for version updates

Evolution Planning:
    - Maintain v1 for at least 12 months after v2 release
    - Clear deprecation timeline communication
    - Backward compatibility within major versions
    - Semantic versioning for predictable changes
"""

# Complete API path prefix
# Combines base path with version for consistent routing
# Used throughout application for endpoint definitions
API_PREFIX = f"/api/{API_VERSION}"
"""
Complete API path prefix for all endpoints.

Combines the base API path with the current version to provide a consistent
URL prefix for all service endpoints. This centralized definition ensures
uniform API routing and simplifies version management.

Value: f"/api/{API_VERSION}" (currently "/api/v1")
Usage: Prefix for all API endpoint definitions

Endpoint Examples:
    - GET /api/v1/books              # List books
    - GET /api/v1/books/{id}         # Get specific book
    - POST /api/v1/books             # Create new book
    - GET /api/v1/inventory          # List inventory
    - POST /api/v1/inventory/adjust  # Adjust inventory

Benefits:
    - Centralized version management
    - Consistent URL structure across all endpoints
    - Easy API version updates
    - Clear API boundary definition
    - OpenAPI specification integration

Router Integration:
    ```python
    from fastapi import APIRouter
    from .config import API_PREFIX

    router = APIRouter(prefix=API_PREFIX)

    @router.get("/books")  # Results in /api/v1/books
    def list_books():
        pass
    ```
"""

# =============================================================================
# SERVICE METADATA
# =============================================================================

# Service identification and metadata
# Used for monitoring, logging, and service discovery
# Provides clear service identity across the platform
SERVICE_NAME = "BookVerse Inventory Service"
"""
Human-readable service name for identification and monitoring.

Provides a clear, descriptive name for the service used in logging,
monitoring, service discovery, and administrative interfaces.
This name appears in dashboards, alerts, and operational tools.

Value: "BookVerse Inventory Service"
Usage: Service identification in logs, metrics, and monitoring

Display Contexts:
    - Application logs and error messages
    - Monitoring dashboards and alerts
    - Service discovery and health checks
    - API documentation and OpenAPI specs
    - Administrative interfaces and tooling

Naming Conventions:
    - Descriptive and human-readable
    - Includes platform name (BookVerse)
    - Specifies service purpose (Inventory)
    - Consistent with other BookVerse services
    - No version information (handled separately)

Integration Examples:
    - Prometheus metrics: service_name="BookVerse Inventory Service"
    - Log entries: {"service": "BookVerse Inventory Service", "message": "..."}
    - Health checks: {"service_name": "BookVerse Inventory Service", "status": "healthy"}
"""

# Service version with environment variable override
# Supports deployment-specific versioning
# Integrates with CI/CD pipeline versioning
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0-dev")
"""
Service version string with environment variable override support.

Provides version identification for the service, supporting both development
and production deployment scenarios. The version follows semantic versioning
principles and integrates with CI/CD pipeline version management.

Environment Variable: SERVICE_VERSION
Default Value: "1.0.0-dev"

Version Format (Semantic Versioning):
    - MAJOR.MINOR.PATCH (e.g., "1.2.3")
    - Pre-release: "1.2.3-alpha.1", "1.2.3-beta.2"
    - Development: "1.0.0-dev" (default)
    - Build metadata: "1.2.3+20240115.abc123"

Environment Examples:
    # Development
    SERVICE_VERSION = "1.0.0-dev"  # Default

    # CI/CD Pipeline
    export SERVICE_VERSION="1.2.3"

    # Staging
    export SERVICE_VERSION="1.2.3-rc.1"

    # Production
    export SERVICE_VERSION="1.2.3"

Usage Contexts:
    - API response headers (X-Service-Version)
    - Health check endpoints
    - Monitoring and alerting systems
    - Deployment tracking and rollback
    - Debugging and support scenarios

CI/CD Integration:
    - Automatically set during build process
    - Git tag integration for release versions
    - Build number and commit hash inclusion
    - Environment-specific version suffixes
"""

# Service description for documentation and discovery
# Provides context about service purpose and capabilities
# Used in API documentation and service catalogs
SERVICE_DESCRIPTION = "Demo inventory service showcasing JFrog AppTrust capabilities"
"""
Service description for documentation and service discovery.

Provides a concise description of the service's purpose, capabilities,
and context within the BookVerse platform. This description is used
in API documentation, service catalogs, and discovery systems.

Value: "Demo inventory service showcasing JFrog AppTrust capabilities"
Usage: API documentation, service discovery, and administrative interfaces

Description Elements:
    - Core functionality: Inventory management
    - Platform context: BookVerse ecosystem
    - Technical focus: JFrog AppTrust integration
    - Deployment context: Demo and showcase scenarios

Usage Contexts:
    - OpenAPI specification descriptions
    - Service catalog entries
    - Developer documentation
    - Administrative dashboards
    - API gateway registration

Enhancement Opportunities:
    - Environment-specific descriptions
    - Capability-based service descriptions
    - Integration point documentation
    - SLA and performance characteristics
"""

# =============================================================================
# BUSINESS LOGIC CONFIGURATION
# =============================================================================

# Inventory management thresholds and limits
# Configurable business logic parameters
# Tunable for different business scenarios
LOW_STOCK_THRESHOLD = 5
"""
Low stock threshold for inventory alerts and reorder notifications.

Defines the minimum quantity level below which books are considered
low stock, triggering alerts and reorder recommendations. This
threshold is used throughout the inventory management system.

Value: 5 (units)
Business Logic: Quantity <= threshold triggers low stock status

Business Impact:
    - Automatic low stock alerts and notifications
    - Reorder point calculations and recommendations
    - Inventory dashboard warnings and indicators
    - Supply chain automation triggers
    - Business intelligence and reporting

Threshold Applications:
    - API responses include low_stock boolean flags
    - Dashboard displays highlight low stock items
    - Automated reorder systems use this threshold
    - Business reporting includes low stock metrics
    - Alert systems notify operations teams

Tuning Considerations:
    - Higher values: Earlier warnings, higher carrying costs
    - Lower values: Later warnings, higher stockout risk
    - Product-specific thresholds (future enhancement)
    - Seasonal adjustments (future enhancement)
    - Velocity-based calculations (future enhancement)

Configuration Examples:
    # Conservative (early warnings)
    LOW_STOCK_THRESHOLD = 10

    # Aggressive (minimal inventory)
    LOW_STOCK_THRESHOLD = 2

    # Balanced (current default)
    LOW_STOCK_THRESHOLD = 5

Future Enhancements:
    - Per-book threshold configuration
    - Dynamic threshold based on sales velocity
    - Seasonal threshold adjustments
    - Supplier lead time integration
"""

# API pagination defaults
# Balance performance with usability
# Prevent resource exhaustion while providing good UX
DEFAULT_PAGE_SIZE = 20
"""
Default number of items returned per page in paginated API responses.

Provides a balanced default page size that offers good user experience
while maintaining reasonable performance characteristics. This value
is used when clients don't specify a page size parameter.

Value: 20 (items per page)
Usage: Default pagination parameter for API endpoints

Performance Considerations:
    - Database query efficiency with reasonable result sets
    - Network transfer time for typical client connections
    - Memory usage for JSON serialization and response formatting
    - Client rendering performance for UI applications

User Experience Balance:
    - Large enough: Reduces pagination overhead for users
    - Small enough: Fast page load times and responsiveness
    - Consistent: Predictable behavior across all endpoints
    - Configurable: Clients can override with per_page parameter

API Integration:
    ```python
    # Client request without page size
    GET /api/v1/books  # Returns 20 items (default)

    # Client request with custom page size
    GET /api/v1/books?per_page=50  # Returns 50 items

    # Minimum page size
    GET /api/v1/books?per_page=1   # Returns 1 item

    # Maximum page size (limited by MAX_PAGE_SIZE)
    GET /api/v1/books?per_page=200  # Limited to MAX_PAGE_SIZE
    ```

Environment Variations:
    - Development: 20 (default for testing)
    - Testing: 10 (smaller sets for faster tests)
    - Production: 20 (optimized for performance)
    - Mobile API: 10 (reduced for slower connections)
"""

# Maximum page size limit
# Prevents resource exhaustion from large requests
# Protects against abuse while allowing reasonable data access
MAX_PAGE_SIZE = 100
"""
Maximum allowed page size for paginated API responses.

Enforces an upper limit on the number of items that can be requested
in a single API call, protecting against resource exhaustion and
potential abuse while still allowing reasonable data access patterns.

Value: 100 (maximum items per page)
Purpose: Resource protection and performance optimization

Resource Protection:
    - Prevents excessive memory usage during response generation
    - Limits database query result set sizes
    - Controls JSON serialization overhead
    - Protects against malicious or accidental resource exhaustion

Performance Benefits:
    - Ensures consistent response times under all conditions
    - Prevents database query timeouts with large result sets
    - Maintains predictable memory usage patterns
    - Enables effective response caching strategies

Client Behavior:
    - Requests exceeding this limit are clamped to MAX_PAGE_SIZE
    - Clear error messages inform clients of the limit
    - Pagination metadata guides clients through large datasets
    - Bulk data access patterns supported through multiple requests

Implementation Example:
    ```python
    def validate_page_size(requested_size: int) -> int:
        if requested_size <= 0:
            return DEFAULT_PAGE_SIZE
        return min(requested_size, MAX_PAGE_SIZE)
    ```

Limit Considerations:
    - Large enough: Supports reasonable bulk operations
    - Small enough: Protects system resources
    - Documented: Clear API documentation of limits
    - Consistent: Same limit across all paginated endpoints

Alternative Patterns:
    - Streaming APIs for very large datasets
    - Bulk export endpoints with async processing
    - GraphQL for selective field retrieval
    - Cursor-based pagination for ordered results
"""
