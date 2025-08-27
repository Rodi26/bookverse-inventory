# BookVerse Inventory Service - Design & Architecture

## 📋 Service Overview

The **BookVerse Inventory Service** is the foundational microservice responsible for managing the complete book catalog, inventory levels, and availability tracking across the BookVerse platform. It serves as the authoritative source for all book-related data and inventory operations.

### Business Requirements

**Core Functionality:**
- ✅ **Book Catalog Management**: Simple book metadata (title, authors, genres, etc.)
- ✅ **Basic Inventory Tracking**: Stock levels for online shop
- ✅ **Availability Queries**: Check if books are in stock
- ✅ **Simple Stock Operations**: Basic inventory adjustments (stock in/out)

**Non-Functional Requirements:**
- 🚀 **Performance**: <200ms response time for catalog queries
- 🔄 **Reliability**: 95% uptime with basic error handling

## 🏗️ Architecture Design

### Service Architecture Pattern
```
┌─────────────────────────────────────────────────────────┐
│                    API Gateway                          │
│                  (Future: Kong/NGINX)                   │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│               BookVerse Inventory Service               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   API       │  │  Business   │  │    Data     │     │
│  │   Layer     │  │   Logic     │  │    Layer    │     │
│  │  (FastAPI)  │  │   Layer     │  │ (SQLAlchemy)│     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                  Data Storage                           │
│  ┌─────────────┐              ┌─────────────┐          │
│  │  PostgreSQL │              │    Redis    │          │
│  │ (Primary DB)│              │   (Cache)   │          │
│  └─────────────┘              └─────────────┘          │
└─────────────────────────────────────────────────────────┘
```

### Technology Stack

**Core Framework:**
- **FastAPI 0.111.0**: Modern, fast web framework with automatic OpenAPI documentation
- **Pydantic v2**: Data validation and serialization with type hints
- **SQLAlchemy 2.0**: Modern ORM with async support
- **Alembic**: Database migration management

**Database & Caching:**
- **PostgreSQL 15**: Primary database for persistent storage
- **Redis 7**: In-memory cache for frequently accessed data
- **Connection Pooling**: Optimized database connections

**Development & Testing:**
- **Pytest**: Comprehensive testing framework
- **pytest-asyncio**: Async test support
- **httpx**: Async HTTP client for integration tests
- **Factory Boy**: Test data factories
- **Coverage.py**: Code coverage reporting

**Observability:**
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Prometheus Metrics**: Custom business metrics
- **Health Checks**: Liveness and readiness probes
- **Distributed Tracing**: OpenTelemetry integration (future)

## 📊 Data Models

### Core Entities

```python
# Book Entity
class Book:
    id: UUID                    # Primary key
    title: str                  # Book title
    subtitle: Optional[str]     # Book subtitle
    authors: List[str]          # List of author names
    genres: List[str]           # Book genres/categories
    description: str            # Book description
    price: Decimal              # Base price in USD
    cover_image_url: str        # URL to cover image (mandatory)
    created_at: datetime        # Record creation timestamp
    updated_at: datetime        # Record update timestamp
    is_active: bool = True      # Soft delete flag

# Inventory Entity  
class InventoryRecord:
    id: UUID                    # Primary key
    book_id: UUID               # Foreign key to Book
    quantity_available: int     # Available stock
    quantity_total: int         # Total physical stock
    reorder_point: int          # Minimum stock level
    created_at: datetime        # Record creation timestamp
    updated_at: datetime        # Record update timestamp

# Stock Transaction Entity
class StockTransaction:
    id: UUID                    # Primary key
    book_id: UUID               # Foreign key to Book
    transaction_type: TransactionType  # STOCK_IN, STOCK_OUT, ADJUSTMENT
    quantity_change: int        # Positive or negative quantity change
    timestamp: datetime         # Transaction timestamp
```

### Enums and Constants

```python
class TransactionType(str, Enum):
    STOCK_IN = "stock_in"           # Receiving new inventory
    STOCK_OUT = "stock_out"         # Fulfilling orders
    ADJUSTMENT = "adjustment"       # Manual adjustments
```

## 🌐 API Design

### RESTful API Endpoints

**Book Catalog Management:**
```
GET    /api/v1/books                     # List books with basic pagination
POST   /api/v1/books                     # Create new book
GET    /api/v1/books/{book_id}           # Get book details
PUT    /api/v1/books/{book_id}           # Update book
DELETE /api/v1/books/{book_id}           # Soft delete book
```

**Inventory Management:**
```
GET    /api/v1/inventory                 # List inventory records
GET    /api/v1/inventory/{book_id}       # Get inventory for specific book
POST   /api/v1/inventory/{book_id}/adjust    # Adjust inventory levels
GET    /api/v1/inventory/low-stock       # Get low stock items
```

**Stock Transactions:**
```
GET    /api/v1/transactions              # List stock transactions
GET    /api/v1/transactions/{book_id}    # Get transactions for book
```

**Health & Operations:**
```
GET    /health                           # Health check endpoint
GET    /health/ready                     # Readiness probe
GET    /health/live                      # Liveness probe
GET    /metrics                          # Prometheus metrics
GET    /api/v1/info                      # Service information
```

### API Request/Response Examples

**Book List:**
```json
GET /api/v1/books?limit=10&offset=0

Response:
{
  "books": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "The Lord of the Rings",
      "subtitle": "The Fellowship of the Ring",
      "authors": ["J.R.R. Tolkien"],
      "genres": ["fiction", "fantasy"],
      "description": "The first volume of the epic Lord of the Rings trilogy...",
      "price": "16.99",
      "cover_image_url": "https://example.com/covers/lotr.jpg",
      "availability": {
        "quantity_available": 45,
        "in_stock": true
      }
    }
  ],
  "pagination": {
    "total": 1,
    "limit": 10,
    "offset": 0,
    "has_next": false
  }
}
```

**Inventory Adjustment:**
```json
POST /api/v1/inventory/123e4567-e89b-12d3-a456-426614174000/adjust

Request:
{
  "quantity_change": 100
}

Response:
{
  "transaction_id": "trans-789",
  "book_id": "123e4567-e89b-12d3-a456-426614174000",
  "new_quantity": 120,
  "quantity_change": 100,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🧪 Testing Strategy

### Test Pyramid

**Unit Tests (80%):**
- Business logic validation
- Data model constraints
- API endpoint behavior
- Basic error handling

**Integration Tests (20%):**
- Database operations
- End-to-end API workflows

### Test Data Strategy

**Test Fixtures:**
```python
# Sample test books for consistent testing
TEST_BOOKS = [
    {
        "title": "The Lord of the Rings",
        "subtitle": "The Fellowship of the Ring",
        "authors": ["J.R.R. Tolkien"],
        "genres": ["fiction", "fantasy"],
        "description": "The first volume of the epic Lord of the Rings trilogy...",
        "price": "16.99",
        "cover_image_url": "https://example.com/covers/lotr.jpg"
    },
    # ... more test books
]

# Factory for generating test data
class BookFactory(factory.Factory):
    class Meta:
        model = Book
    
    title = factory.Faker('sentence', nb_words=3)
    subtitle = factory.Faker('sentence', nb_words=2)
    authors = factory.List([factory.Faker('name')])
    genres = factory.List([factory.Faker('word')])
    description = factory.Faker('text')
    price = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True)
    cover_image_url = factory.Faker('image_url')
```

## 🔄 Integration Points

### Service Dependencies

**Internal Services:**
- **Recommendations Service**: Consumes book catalog data
- **Checkout Service**: Validates stock availability during purchase
- **Web Frontend**: Displays book catalog and availability

## 📦 CI/CD & Deployment

### Docker Configuration

**Production Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Configuration

**Development Environment:**
```yaml
# docker-compose.dev.yml
services:
  inventory-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/bookverse_inventory
      - LOG_LEVEL=DEBUG
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=bookverse_inventory
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    ports:
      - "5432:5432"
```

## 🎯 Implementation Plan of Action

### Phase 1: Foundation (Days 1-3)
1. **Project Setup & Structure**
   - ✅ Basic FastAPI application structure
   - ✅ Simplified database models with SQLAlchemy
   - ✅ Basic configuration management
   - ✅ Simple logging setup

2. **Core API Development**
   - ✅ Book CRUD operations
   - ✅ Basic inventory management
   - ✅ Health check endpoints
   - ✅ Auto-generated API documentation

3. **Testing Framework**
   - ✅ Basic unit test setup with pytest
   - ✅ Simple test data fixtures
   - ✅ Basic integration tests

### Phase 2: Core Features (Days 4-6)
4. **Inventory Operations**
   - ✅ Simple inventory adjustments
   - ✅ Low stock monitoring
   - ✅ Basic stock transactions

5. **API Completion**
   - ✅ Complete CRUD for books
   - ✅ Basic pagination for lists
   - ✅ Simple error handling

6. **Testing & Quality**
   - ✅ Good test coverage (>80%)
   - ✅ Integration tests for all endpoints
   - ✅ Basic error scenario testing

### Phase 3: Demo Readiness (Days 7-8)
7. **CI/CD Integration**
   - ✅ GitHub Actions workflow
   - ✅ Docker image building and optimization
   - ✅ JFrog AppTrust integration
   - ✅ SBOM generation and signing

8. **Demo Data & Scenarios**
   - ✅ Realistic book catalog (20+ books)
   - ✅ Demo scenarios scripting
   - ✅ Integration preparation for other services

9. **Documentation & Polish**
   - ✅ Complete API documentation
   - ✅ Demo runbook integration
   - ✅ Basic troubleshooting guide

## 🎪 Demo Scenarios

### Scenario 1: Development Workflow
1. **Code Development**: Add new book to catalog
2. **Local Testing**: Run tests and validate functionality
3. **CI Pipeline**: Trigger GitHub Actions workflow
4. **SBOM Generation**: Automatic SBOM creation and signing
5. **Artifact Publishing**: Push to DEV repository

### Scenario 2: Promotion Pipeline
1. **DEV Validation**: Basic smoke tests in DEV environment
2. **QA Promotion**: Promote artifacts to QA with evidence
3. **STAGING Testing**: Simple integration tests in staging
4. **PROD Release**: Final promotion to production
5. **Audit Trail**: Complete traceability demonstration

### Scenario 3: Inventory Operations
1. **Stock Management**: Add/remove inventory for books
2. **Low Stock Alert**: Demonstrate low stock detection
3. **Transaction History**: Show basic transaction logging
4. **Service Integration**: API calls from other services

## 📈 Success Metrics

**Development Metrics:**
- ✅ Test coverage >80%
- ✅ API response time <200ms
- ✅ Build time <5 minutes
- ✅ Basic functionality working

**Demo Metrics:**
- ✅ Complete DEV→PROD promotion working smoothly
- ✅ SBOM generation and signing functional
- ✅ End-to-end traceability demonstration
- ✅ Core workflows stable during demo

---

This design provides a comprehensive, production-ready inventory service that demonstrates all JFrog AppTrust capabilities while serving as a realistic foundation for the BookVerse platform.
