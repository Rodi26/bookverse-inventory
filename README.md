# BookVerse Inventory Service

Demo-ready FastAPI microservice for the BookVerse platform, showcasing JFrog AppTrust capabilities with multiple artifact types per application version.

## 🎯 Demo Purpose & Patterns

This service demonstrates the **Single Docker Image Application Pattern** - the most common cloud-native deployment approach where application versions are built from a single container image.

### 📦 **Single Docker Image Application Pattern**
- **What it demonstrates**: How to build application versions from a single Docker container image
- **AppTrust benefit**: Simplified artifact promotion - one container moves through all stages (DEV → QA → STAGING → PROD)
- **Real-world applicability**: Most modern cloud-native applications follow this pattern

### 🔄 **Multi-Artifact Application Versions**
- **What it demonstrates**: Application versions composed of multiple artifact types
- **Artifacts created**: Docker images, Python packages, SBOMs, test reports, build evidence
- **AppTrust benefit**: All artifacts are promoted together as a cohesive application version

### 📊 **Realistic Demo Data**
- **What it demonstrates**: How to build compelling demos with realistic business context
- **Demo elements**: 20 professional book catalog, realistic inventory operations, transaction history
- **Business value**: Stakeholders can easily understand and relate to the bookstore scenario

This service is **intentionally comprehensive** - it's not just a "hello world" but a realistic microservice that teams can learn from and adapt to their own use cases.
## 🏁 Quick Start

### Docker (Recommended)

```bash
# Run the service with Docker
docker build -t bookverse-inventory .
docker run -p 8000:8000 \
  -e AUTH_ENABLED=false \
  -e LOG_LEVEL=INFO \
  bookverse-inventory

# Access the service
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/books
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt
pip install -e libs/bookverse-core

# Set environment variables
export AUTH_ENABLED=false
export LOG_LEVEL=DEBUG

# Initialize demo data
python scripts/download_images.py

# Run the service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
python -m pytest tests/ -v --cov=app
```

### Python Package

```bash
# Build package
python -m build

# Install package
pip install dist/bookverse_inventory-*.whl

# Run as package
bookverse-inventory
```

## 📊 API Endpoints

### Service Information
- `GET /info` - Service metadata and configuration details
- `GET /health` - Basic health check
- `GET /health/live` - Liveness probe for Kubernetes
- `GET /health/ready` - Readiness probe with dependency checks
- `GET /health/status` - Detailed health information

### Book Catalog Management
- `GET /api/v1/books` - List books with pagination and filtering
- `GET /api/v1/books/{id}` - Get specific book details
- `POST /api/v1/books` - Create new book (requires authentication)
- `PUT /api/v1/books/{id}` - Update book information (requires authentication)
- `DELETE /api/v1/books/{id}` - Remove book from catalog (requires authentication)

### Inventory Operations
- `GET /api/v1/inventory` - List inventory records with stock levels
- `GET /api/v1/inventory/{book_id}` - Get specific book inventory details
- `POST /api/v1/inventory/adjust` - Adjust stock levels with audit trail
- `GET /api/v1/transactions` - View inventory transaction history

### Example API Usage

```bash
# List books with pagination
curl "http://localhost:8000/api/v1/books?page=1&per_page=10"

# Get service information
curl "http://localhost:8000/info"

# Check inventory for a book
curl "http://localhost:8000/api/v1/inventory/book-uuid-here"

# Adjust inventory (requires auth when enabled)
curl -X POST "http://localhost:8000/api/v1/inventory/adjust" \
  -H "Content-Type: application/json" \
  -d '{"book_id": "book-uuid", "quantity_change": -5, "reason": "sale"}'
```

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_VERSION` | `1.0.0-dev` | Service version identifier |
| `DATABASE_URL` | `sqlite:///./bookverse_inventory.db` | Database connection string |
| `LOG_LEVEL` | `INFO` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |
| `AUTH_ENABLED` | `true` | Enable/disable authentication middleware |
| `ENVIRONMENT` | `development` | Runtime environment context |
| `LOW_STOCK_THRESHOLD` | `5` | Threshold for low stock alerts |
| `DEFAULT_PAGE_SIZE` | `20` | Default pagination size |
| `MAX_PAGE_SIZE` | `100` | Maximum allowed page size |

### Database Configuration

**Development (SQLite)**
```bash
DATABASE_URL=sqlite:///./bookverse_inventory.db
```

**Production (PostgreSQL)**
```bash
DATABASE_URL=postgresql://user:password@host:5432/bookverse_inventory
```

## 🏗️ Architecture

### Service Integration
The Inventory Service integrates with the BookVerse ecosystem:

```
┌─────────────────┐    ┌───────────────────┐    ┌─────────────────┐
│   Web Frontend  │────│  Platform Service │────│ Checkout Service│
└─────────────────┘    └───────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────│ Inventory Service│──────────────┘
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │Recommendations  │
                        │    Service      │
                        └─────────────────┘
```

### Internal Components
- **FastAPI Application** - ASGI-based async web framework
- **SQLAlchemy ORM** - Database abstraction with async support
- **BookVerse Core** - Shared utilities and middleware
- **Pydantic Models** - Request/response validation
- **Middleware Stack** - Authentication, logging, CORS, request ID tracking

## 🔧 JFrog AppTrust Integration

This service creates multiple artifacts per application version:

1. **Python Packages** - Wheel and source distributions
2. **Docker Images** - Containerized service with health checks
3. **SBOMs** - Software Bill of Materials for both Python and Docker
4. **Test Reports** - Coverage and test results
5. **Build Evidence** - Comprehensive build and security attestations

Each artifact moves together through the promotion pipeline: DEV → QA → STAGING → PROD.

For the non-JFrog evidence plan and gates, see: `../bookverse-demo-init/docs/EVIDENCE_PLAN.md`.

## 📚 Demo Data

The service includes 20 professionally curated books with:

- Real cover images from Goodreads
- Proper metadata (authors, genres, descriptions)  
- Realistic inventory levels (some with low stock)
- Pre-populated transaction history
- Perfect for demonstrating a realistic bookshop inventory system!

## 🚀 Performance Specifications

- **Target Response Time**: < 100ms for catalog operations
- **Throughput**: 2000+ requests per second with proper caching
- **Concurrency**: Full async/await support for high-concurrency operations
- **Database**: SQLite with connection pooling (PostgreSQL recommended for production)

## 📋 Required Repository Configuration

### Repository Variables
- `PROJECT_KEY`: `bookverse`
- `DOCKER_REGISTRY`: e.g., `releases.jfrog.io` (or your Artifactory Docker registry host)
- `JFROG_URL`: e.g., `https://releases.jfrog.io`

### Repository Secrets
- `EVIDENCE_PRIVATE_KEY`: Private key PEM for evidence signing (mandatory)

### Mandatory OIDC Application Binding

This repository must include a committed `.jfrog/config.yml` declaring the AppTrust application key:

Path: `bookverse-inventory/.jfrog/config.yml`

```yaml
application:
  key: "bookverse-inventory"
```

## 🔄 Workflows

- [`ci.yml`](.github/workflows/ci.yml) — CI: tests, package build, Docker build, publish artifacts/build-info, AppTrust version and evidence
- [`promote.yml`](.github/workflows/promote.yml) — Promote the inventory app version through stages with evidence
- [`promotion-rollback.yml`](.github/workflows/promotion-rollback.yml) — Roll back a promoted inventory application version (demo utility)

### OIDC-based Rollback (No Tokens Required)

```bash
# Local usage (requires jf CLI configured)
jf c add --interactive=false --url "$JFROG_URL" --access-token ""

# Run rollback script
python bookverse-infra/libraries/bookverse-devops/scripts/apptrust_rollback.py \
  --app bookverse-inventory --version 1.2.3
```

## 🛠️ Development

### Code Quality

```bash
# Format code
black app/ tests/
isort app/ tests/

# Lint code  
flake8 app/ tests/

# Type checking
mypy app/
```

### Testing

```bash
# Run all tests with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py -v

# View coverage report
open htmlcov/index.html
```

## 📖 API Documentation

When running the service, interactive documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🐛 Troubleshooting

### Common Issues

**Service won't start**
```bash
# Check logs
docker logs bookverse-inventory

# Verify database connectivity
curl http://localhost:8000/health/ready
```

**Authentication errors** 
```bash
# Disable auth for testing
export AUTH_ENABLED=false

# Check auth status
curl http://localhost:8000/auth/status
```

**Database connection issues**
```bash
# Verify DATABASE_URL format
echo $DATABASE_URL

# Test connectivity
python -c "from app.database import engine; print('DB OK')"
```

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- **Issues**: GitHub Issues
- **Documentation**: `/docs` endpoint when running
- **Health Status**: `/health/status` endpoint
