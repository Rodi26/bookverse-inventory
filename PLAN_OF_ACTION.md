# BookVerse Inventory Service - Implementation Plan of Action

## 🎯 Project Overview

Transform the basic FastAPI scaffold into a demo-ready inventory service that demonstrates core JFrog AppTrust capabilities including SBOM generation, artifact signing, promotion workflows, and basic traceability. Focus on simplicity while maintaining demo value.

## 📋 Implementation Phases

### 🏗️ Phase 1: Foundation Setup (Days 1-3)

#### Task 1.1: Project Structure & Dependencies
**Goal**: Establish clean project foundation with demo-focused simplicity

**Deliverables:**
- ✅ Simple directory structure with clear organization
- ✅ Updated requirements.txt with essential dependencies
- ✅ Basic configuration management
- ✅ Simple logging setup

**Technical Tasks:**
```bash
# New project structure
bookverse-inventory/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── database.py             # Database connection and session
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── book.py
│   │   ├── inventory.py
│   │   └── transaction.py
│   ├── schemas/                # Pydantic models
│   │   ├── __init__.py
│   │   ├── book.py
│   │   ├── inventory.py
│   │   └── response.py
│   ├── services/               # Business logic layer
│   │   ├── __init__.py
│   │   ├── book_service.py
│   │   └── inventory_service.py
│   ├── api/                    # API route handlers
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── books.py
│   │   │   ├── inventory.py
│   │   │   └── health.py
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       ├── logging.py
│       └── exceptions.py
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py            # Pytest configuration
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── fixtures/              # Test data
├── migrations/                 # Alembic migrations
├── docker-compose.dev.yml     # Development environment
└── pyproject.toml             # Modern Python project configuration
```

#### Task 1.2: Database Models & Migrations
**Goal**: Implement robust data models with proper relationships

**Deliverables:**
- ✅ SQLAlchemy models for Book, InventoryRecord, StockTransaction
- ✅ Database migration system with Alembic
- ✅ Proper indexes and constraints
- ✅ Soft delete implementation

**Database Schema:**
```sql
-- Books table
CREATE TABLE books (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    subtitle VARCHAR(500),
    authors JSONB NOT NULL,
    genres JSONB NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    cover_image_url VARCHAR(1000) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Inventory records table
CREATE TABLE inventory_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID NOT NULL REFERENCES books(id) UNIQUE,
    quantity_available INTEGER NOT NULL DEFAULT 0,
    quantity_total INTEGER NOT NULL DEFAULT 0,
    reorder_point INTEGER NOT NULL DEFAULT 5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Stock transactions table
CREATE TABLE stock_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID NOT NULL REFERENCES books(id),
    transaction_type VARCHAR(20) NOT NULL,
    quantity_change INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Task 1.3: Core API Framework
**Goal**: Implement FastAPI application with proper structure

**Deliverables:**
- ✅ FastAPI app with versioned API routes
- ✅ Automatic OpenAPI documentation
- ✅ Request/response validation with Pydantic
- ✅ Error handling middleware
- ✅ Health check endpoints

### 🚀 Phase 2: Core Functionality (Days 4-6)

#### Task 2.1: Book Management API
**Goal**: Simple CRUD operations for book catalog

**API Endpoints:**
```python
# Book catalog endpoints
@router.get("/books", response_model=BookListResponse)
async def list_books(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List books with basic pagination"""

@router.post("/books", response_model=BookResponse, status_code=201)
async def create_book(book: BookCreateRequest):
    """Create new book"""

@router.get("/books/{book_id}", response_model=BookDetailResponse)
async def get_book(book_id: UUID):
    """Get book details"""

@router.put("/books/{book_id}", response_model=BookResponse)
async def update_book(book_id: UUID, book: BookUpdateRequest):
    """Update book information"""

@router.delete("/books/{book_id}", status_code=204)
async def delete_book(book_id: UUID):
    """Soft delete book"""
```

**Business Logic:**
- ✅ Basic book validation with Pydantic
- ✅ Simple CRUD operations
- ✅ Soft delete implementation
- ✅ Basic error handling

#### Task 2.2: Inventory Management API
**Goal**: Simple inventory operations for demo

**API Endpoints:**
```python
# Inventory management endpoints
@router.get("/inventory", response_model=InventoryListResponse)
async def list_inventory(
    low_stock: bool = False,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List inventory records"""

@router.get("/inventory/{book_id}", response_model=InventoryDetailResponse)
async def get_book_inventory(book_id: UUID):
    """Get inventory for specific book"""

@router.post("/inventory/{book_id}/adjust", response_model=TransactionResponse)
async def adjust_inventory(
    book_id: UUID,
    adjustment: InventoryAdjustmentRequest
):
    """Adjust inventory levels"""

@router.get("/inventory/low-stock", response_model=InventoryListResponse)
async def get_low_stock():
    """Get books with low stock"""
```

**Business Logic:**
- ✅ Basic inventory operations
- ✅ Simple stock validation
- ✅ Low stock detection
- ✅ Basic transaction logging

#### Task 2.3: Testing Framework Implementation
**Goal**: Good test coverage for demo reliability

**Test Structure:**
```python
# Unit tests
tests/unit/
├── test_book_service.py        # Book operations tests
├── test_inventory_service.py   # Inventory operations tests
└── test_models.py              # Database model tests

# Integration tests  
tests/integration/
├── test_book_api.py            # Book API endpoint tests
├── test_inventory_api.py       # Inventory API endpoint tests
└── test_health.py              # Health check tests

# Test fixtures
tests/fixtures/
└── sample_books.json           # Sample test data
```

**Test Coverage Goals:**
- ✅ >80% code coverage
- ✅ All main API endpoints tested
- ✅ Basic error scenarios covered
- ✅ Health checks validated

### 🔄 Phase 3: Demo Readiness (Days 7-8)

#### Task 3.1: CI/CD Integration
**Goal**: Complete JFrog AppTrust integration for demo (OIDC-only)

**Features:**
- ✅ GitHub Actions workflow optimization
- ✅ Docker image building and security scanning
- ✅ JFrog Platform integration (SBOM, signing, promotion)
- ✅ Automated testing in CI pipeline

#### Task 3.2: Demo Data & Scenarios
**Goal**: Realistic demo data and scenarios

**Features:**
- ✅ Sample book catalog (20+ books with cover images)
- ✅ Initial inventory data
- ✅ Demo scenario scripts
- ✅ API integration examples for other services

#### Task 3.3: Documentation & Polish

**Goal**: Complete documentation for demo execution

**Features:**
- ✅ OpenAPI documentation refinement
- ✅ Demo runbook integration
- ✅ Basic logging and health checks
- ✅ Error handling improvements

## 📊 Success Criteria & Validation

### Technical Validation

- ✅ **Test Coverage**: >80% code coverage with good test suite
- ✅ **Performance**: <200ms response time for basic queries
- ✅ **Reliability**: Stable operations during demo
- ✅ **Functionality**: All core features working properly

### Demo Validation

- ✅ **CI/CD Pipeline**: Complete build → test → SBOM → sign → publish cycle
- ✅ **AppTrust Integration**: Full artifact lifecycle through DEV → QA → STAGING → PROD
- ✅ **Traceability**: Basic audit trail from code commit to deployment
- ✅ **Stability**: Service runs reliably during demo scenarios




## 🚀 Getting Started

### Immediate Next Steps

1. **Review Simplified Design**: Understand the streamlined architecture focused on demo value
2. **Set Up Development Environment**: Local Docker container for PostgreSQL
3. **Begin Phase 1**: Start with basic project structure and database models
4. **Focus on CI/CD Integration**: Prioritize JFrog AppTrust demonstration capabilities

### Development Environment Setup

```bash
# Current directory: bookverse-inventory/
cd /Users/yonatanp/playground/AppTrust-BookVerse/bookverse-demo/bookverse-inventory

# Start development database
docker-compose -f docker-compose.dev.yml up -d

# Install dependencies (when ready)
pip install -r requirements.txt

# Start development server (when ready)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Key Simplifications for Demo Success

- **8-day timeline** instead of 12 days
- **No complex features** like search, reservations, or advanced caching
- **Simple data models** focused on core book and inventory operations
- **Basic CI/CD integration** with strong JFrog AppTrust demonstration value
- **20+ sample books** for realistic demo scenarios
- **Online shop only** - no multiple locations or complex logistics

This simplified plan provides a clear, executable roadmap for building a demo-ready inventory service that perfectly demonstrates JFrog AppTrust capabilities while remaining achievable and maintainable!

---

## 🔐 OIDC-Only Authentication Plan (Tokenless Services)

### Goals

- Remove `JFROG_ADMIN_TOKEN` and `JFROG_ACCESS_TOKEN` from this repository.
- Use GitHub Actions OIDC + JFrog CLI for all CI authentication.
- Keep admin/bootstrap operations centralized in `bookverse-demo-init`.

### Changes

- Rollback utility supports OIDC via `jf curl` and no longer requires tokens.
- README updated: secrets list excludes JFROG tokens; documents OIDC rollback.
- Future workflows should login via OIDC using `jfrog/setup-jfrog-cli` and configured server context.

### Rollback Flow (OIDC)

1. CI obtains an OIDC token automatically via `jfrog/setup-jfrog-cli`.
2. `scripts/apptrust_rollback.py` uses JFrog CLI (`jf curl`) to call AppTrust APIs without a bearer token.
3. No long-lived tokens exist in this repo or its Actions secrets.

### Fallback for Local Testing

- Developers may pass `--token` and `--base-url` to the rollback script when working outside CI.
- This does not reintroduce tokens into the repository or CI; it's a local convenience only.
