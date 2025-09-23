# Inventory Service - Development Guide

**Local development setup, testing, and database schema for the BookVerse Inventory Service**

This guide provides everything developers need to set up, develop, test, and debug the Inventory Service locally.

---

## 🛠️ Development Environment Setup

### 📋 **Prerequisites**

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.11+ | Runtime environment |
| **pip** | Latest | Package management |
| **Git** | 2.25+ | Version control |
| **SQLite** | 3.40+ | Database (included with Python) |
| **Docker** | 20.10+ | Container development (optional) |

### 🔧 **Environment Setup**

**1. Clone and Setup:**
```bash
# Clone the repository
git clone https://github.com/your-org/bookverse-inventory.git
cd bookverse-inventory

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

**2. Environment Configuration:**
```bash
# Copy example environment file
cp config/auth.env.example config/auth.env

# Edit configuration
cat > config/auth.env << EOF
# Database Configuration
DATABASE_URL=sqlite:///./bookverse_inventory.db
DATABASE_ECHO=false

# Authentication
JWT_SECRET_KEY=your-secret-key-for-development
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Service Configuration
SERVICE_NAME=bookverse-inventory
SERVICE_VERSION=1.0.0
LOG_LEVEL=DEBUG

# External Services
RECOMMENDATIONS_SERVICE_URL=http://localhost:8001
CHECKOUT_SERVICE_URL=http://localhost:8002
EOF
```

### 🗄️ **Database Setup**

**Initialize Database:**
```bash
# Create database and tables
python -c "
from app.database import engine
from app.models import Base
Base.metadata.create_all(bind=engine)
print('Database initialized successfully')
"

# Load sample data
python scripts/load_sample_data.py
```

**Database Schema Verification:**
```bash
# Verify database structure
sqlite3 bookverse_inventory.db ".schema"

# Check sample data
sqlite3 bookverse_inventory.db "SELECT COUNT(*) FROM books;"
```

---

## 🚀 Running the Service

### 🖥️ **Development Server**

**Standard Development:**
```bash
# Run with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run with debug logging
LOG_LEVEL=DEBUG uvicorn app.main:app --reload --port 8000
```

**Docker Development:**
```bash
# Build development image
docker build -t bookverse-inventory:dev .

# Run container with volume mounts
docker run -p 8000:8000 \
  -v $(pwd)/app:/app/app \
  -v $(pwd)/config:/app/config \
  -e LOG_LEVEL=DEBUG \
  bookverse-inventory:dev
```

### 🌐 **Service Endpoints**

After starting the service:

| Endpoint | URL | Purpose |
|----------|-----|---------|
| **API Documentation** | http://localhost:8000/docs | Interactive API docs |
| **Health Check** | http://localhost:8000/health | Service health status |
| **Metrics** | http://localhost:8000/metrics | Performance metrics |
| **OpenAPI Schema** | http://localhost:8000/openapi.json | API specification |

---

## 🧪 Testing Framework

### 🔧 **Test Configuration**

**Test Environment Setup:**
```bash
# Create test database
export DATABASE_URL=sqlite:///./test_inventory.db

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Verify test setup
pytest --version
```

### 📊 **Running Tests**

**Basic Test Execution:**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test files
pytest tests/test_api.py
pytest tests/test_models.py

# Run tests with verbose output
pytest -v -s
```

**Test Categories:**
```bash
# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# API tests
pytest tests/api/

# Performance tests
pytest tests/performance/ --benchmark-only
```

### 🧩 **Test Structure**

```
tests/
├── conftest.py              # Test configuration and fixtures
├── unit/                    # Unit tests
│   ├── test_models.py       # Database model tests
│   ├── test_services.py     # Business logic tests
│   └── test_schemas.py      # Validation tests
├── integration/             # Integration tests
│   ├── test_database.py     # Database integration
│   └── test_external_apis.py # External service tests
├── api/                     # API endpoint tests
│   ├── test_books.py        # Book endpoints
│   ├── test_search.py       # Search functionality
│   └── test_inventory.py    # Inventory operations
└── performance/             # Performance tests
    ├── test_load.py         # Load testing
    └── test_benchmarks.py   # Performance benchmarks
```

### 🎯 **Test Examples**

**Unit Test Example:**
```python
# tests/unit/test_models.py
import pytest
from app.models import Book
from app.schemas import BookCreate

def test_book_creation():
    """Test book model creation with valid data."""
    book_data = BookCreate(
        title="Python Programming",
        author="Jane Smith",
        isbn="978-0123456789",
        price=29.99,
        genre="technology"
    )
    
    book = Book(**book_data.dict())
    assert book.title == "Python Programming"
    assert book.price == 29.99
    assert book.genre == "technology"

def test_book_validation():
    """Test book model validation."""
    with pytest.raises(ValueError):
        Book(
            title="",  # Invalid: empty title
            author="Jane Smith",
            isbn="invalid-isbn",  # Invalid: wrong format
            price=-10  # Invalid: negative price
        )
```

**API Test Example:**
```python
# tests/api/test_books.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_get_books():
    """Test GET /books endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/books")
        
    assert response.status_code == 200
    data = response.json()
    assert "books" in data
    assert "pagination" in data
    assert isinstance(data["books"], list)

@pytest.mark.asyncio
async def test_search_books():
    """Test book search functionality."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/books/search?q=python&genre=technology")
        
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "query" in data
    assert data["query"] == "python"
```

---

## 🗄️ Database Schema

### 📊 **Core Tables**

**Books Table:**
```sql
CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    isbn VARCHAR(20) UNIQUE NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    genre VARCHAR(100) NOT NULL,
    publication_date DATE,
    rating DECIMAL(3,2),
    image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Stock Table:**
```sql
CREATE TABLE stock (
    book_id INTEGER PRIMARY KEY,
    quantity INTEGER NOT NULL DEFAULT 0,
    reserved INTEGER NOT NULL DEFAULT 0,
    available INTEGER GENERATED ALWAYS AS (quantity - reserved) VIRTUAL,
    reorder_point INTEGER NOT NULL DEFAULT 10,
    max_stock INTEGER NOT NULL DEFAULT 100,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books (id)
);
```

**Reservations Table:**
```sql
CREATE TABLE reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    reservation_id VARCHAR(100) UNIQUE NOT NULL,
    customer_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active',
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books (id)
);
```

### 🔄 **Database Migrations**

**Migration Commands:**
```bash
# Generate migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Check migration status
alembic current
```

**Sample Migration:**
```python
# migrations/versions/001_initial.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create books table
    op.create_table(
        'books',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('author', sa.String(255), nullable=False),
        sa.Column('isbn', sa.String(20), nullable=False),
        sa.Column('price', sa.DECIMAL(10,2), nullable=False),
        sa.Column('genre', sa.String(100), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('isbn')
    )

def downgrade():
    op.drop_table('books')
```

---

## 🔧 Development Tools

### 🧹 **Code Quality**

**Linting and Formatting:**
```bash
# Format code with black
black app/ tests/

# Sort imports with isort
isort app/ tests/

# Lint with flake8
flake8 app/ tests/

# Type checking with mypy
mypy app/

# Security scanning with bandit
bandit -r app/
```

**Pre-commit Hooks:**
```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### 📊 **Performance Profiling**

**Database Query Profiling:**
```python
# Enable SQL query logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Profile database queries
from app.database import SessionLocal
from sqlalchemy import event

@event.listens_for(SessionLocal, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(SessionLocal, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    print(f"Query took {total:.4f}s: {statement[:50]}")
```

**API Performance Testing:**
```bash
# Install locust for load testing
pip install locust

# Run load tests
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

### 🐛 **Debugging**

**Debug Configuration:**
```python
# app/main.py - Add debug middleware
if settings.DEBUG:
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))
    print("Debugger listening on port 5678")
```

**Database Debug Queries:**
```bash
# SQLite CLI for debugging
sqlite3 bookverse_inventory.db

# Common debug queries
.tables                              # List all tables
.schema books                        # Show table schema
SELECT * FROM books LIMIT 5;        # Sample data
EXPLAIN QUERY PLAN SELECT * FROM books WHERE genre = 'technology';
```

---

## 🔍 API Development

### 📝 **Adding New Endpoints**

**1. Define Schema (schemas.py):**
```python
from pydantic import BaseModel
from typing import Optional

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Updated Book Title",
                "price": 24.99
            }
        }
```

**2. Add Database Model (models.py):**
```python
from sqlalchemy import Column, Integer, String, DateTime, func

class BookHistory(Base):
    __tablename__ = "book_history"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    action = Column(String(50), nullable=False)
    changes = Column(JSON)
    timestamp = Column(DateTime, default=func.now())
```

**3. Implement Endpoint (api.py):**
```python
@router.put("/books/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: int,
    book_update: BookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update book information."""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Update fields
    for field, value in book_update.dict(exclude_unset=True).items():
        setattr(book, field, value)
    
    db.commit()
    db.refresh(book)
    return book
```

**4. Add Tests:**
```python
@pytest.mark.asyncio
async def test_update_book():
    """Test book update endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create test book first
        book_data = {"title": "Test Book", "author": "Test Author"}
        create_response = await client.post("/books", json=book_data)
        book_id = create_response.json()["id"]
        
        # Update book
        update_data = {"title": "Updated Title"}
        response = await client.put(f"/books/{book_id}", json=update_data)
        
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"
```

---

## 🔧 Configuration Management

### ⚙️ **Configuration Files**

**config/settings.py:**
```python
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./bookverse_inventory.db"
    database_echo: bool = False
    
    # Authentication
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # Service
    service_name: str = "bookverse-inventory"
    service_version: str = "1.0.0"
    log_level: str = "INFO"
    
    # External Services
    recommendations_service_url: Optional[str] = None
    checkout_service_url: Optional[str] = None
    
    class Config:
        env_file = "config/auth.env"

settings = Settings()
```

### 🔐 **Environment Variables**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | No | SQLite local | Database connection string |
| `JWT_SECRET_KEY` | Yes | - | JWT signing secret |
| `LOG_LEVEL` | No | INFO | Logging level |
| `SERVICE_PORT` | No | 8000 | Service port |
| `RECOMMENDATIONS_SERVICE_URL` | No | - | Recommendations service endpoint |

---

## 📞 Development Support

### 🤝 **Getting Help**
- **📖 [Service Overview](SERVICE_OVERVIEW.md)** - Business context and capabilities
- **📚 [API Reference](API_REFERENCE.md)** - Complete API documentation
- **🚀 [Deployment Guide](DEPLOYMENT.md)** - Production deployment
- **🐛 [Issue Tracker](../../issues)** - Bug reports and feature requests

### 🔧 **Development Resources**
- **📝 [Code Examples](../examples/)** - Implementation patterns
- **⚡ [Performance Guide](../performance/)** - Optimization strategies
- **🔐 [Security Guide](../security/)** - Security best practices
- **💬 [Developer Discussions](../../discussions)** - Community support

---

*This development guide is continuously updated based on developer feedback. For questions or improvements, please engage with our [developer community](../../discussions).*
