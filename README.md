# BookVerse Inventory Service

Demo-ready FastAPI microservice for the BookVerse platform, showcasing JFrog AppTrust capabilities with multiple artifact types per application version.

## Features

- 📚 **Complete Book Catalog** - 20 professional demo books with realistic metadata
- 📊 **Inventory Management** - Stock levels, low stock alerts, availability tracking
- 🔄 **Transaction Logging** - Basic audit trail for stock operations
- 🐳 **Container Ready** - Optimized Docker builds with health checks
- 🧪 **Comprehensive Testing** - Unit and integration tests with coverage
- 📋 **Multiple Artifacts** - Python packages, Docker images, SBOMs for JFrog AppTrust

## Quick Start

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
python -m pytest tests/ -v
```

### Docker
```bash
docker build -t bookverse-inventory .
docker run -p 8000:8000 bookverse-inventory
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

## API Endpoints

- `GET /health` - Health check and database status
- `GET /api/v1/books` - List books with availability
- `GET /api/v1/inventory` - List inventory records
- `POST /api/v1/inventory/adjust` - Adjust stock levels
- `GET /api/v1/transactions` - View transaction history

## JFrog AppTrust Integration

This service creates multiple artifacts per application version:

1. **Python Packages** - Wheel and source distributions
2. **Docker Images** - Containerized service
3. **SBOMs** - Software Bill of Materials for both Python and Docker
4. **Test Reports** - Coverage and test results

Each artifact moves together through the promotion pipeline: DEV → QA → STAGING → PROD.

For the non-JFrog evidence plan and gates, see: `../bookverse-demo-init/docs/EVIDENCE_PLAN.md`.

## Demo Data

The service includes 20 professionally curated books with:
- Real cover images from Goodreads
- Proper metadata (authors, genres, descriptions)
- Realistic inventory levels (some with low stock)
- Pre-populated transaction history

Perfect for demonstrating a realistic bookshop inventory system!
🧪 Testing evidence creation fix - Thu Aug 28 17:02:24 IDT 2025
🧪 Testing SHA256 digest fix - Thu Aug 28 17:13:17 IDT 2025
🔄 Testing CORRECT Docker evidence format - Thu Aug 28 17:26:46 IDT 2025

## Required repository variables

- `PROJECT_KEY`: `bookverse`
- `DOCKER_REGISTRY`: e.g., `releases.jfrog.io` (or your Artifactory Docker registry host)
- `JFROG_URL`: e.g., `https://releases.jfrog.io`

## Required repository secrets

- `JFROG_ACCESS_TOKEN`: Access token used by CI to interact with JFrog Platform
- `EVIDENCE_PRIVATE_KEY`: Private key PEM for evidence signing (mandatory)

## Workflows

- [`ci.yml`](.github/workflows/ci.yml) — CI: tests, package build, Docker build, publish artifacts/build-info, AppTrust version and evidence.
- [`promote.yml`](.github/workflows/promote.yml) — Promote the inventory app version through stages with evidence.
- [`promotion-rollback.yml`](.github/workflows/promotion-rollback.yml) — Roll back a promoted inventory application version (demo utility).
