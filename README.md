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

## 🔧 JFrog AppTrust Integration

This service creates multiple artifacts per application version:

1. **Python Packages** - Wheel and source distributions
2. **Docker Images** - Containerized service with health checks
3. **SBOMs** - Software Bill of Materials for both Python and Docker
4. **Test Reports** - Coverage and test results
5. **Build Evidence** - Comprehensive build and security attestations

Each artifact moves together through the promotion pipeline: DEV → QA → STAGING → PROD.

For the non-JFrog evidence plan and gates, see: `../bookverse-demo-init/docs/EVIDENCE_PLAN.md`.

## 🔄 Workflows

- [`ci.yml`](.github/workflows/ci.yml) — CI: tests, package build, Docker build, publish artifacts/build-info, AppTrust version and evidence
- [`promote.yml`](.github/workflows/promote.yml) — Promote the inventory app version through stages with evidence
- [`promotion-rollback.yml`](.github/workflows/promotion-rollback.yml) — Roll back a promoted inventory application version (demo utility)
