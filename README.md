# BookVerse Inventory Service

This repository is part of the JFrog AppTrust BookVerse demo. The demo showcases a secure software supply chain using JFrog Platform capabilities: AppTrust lifecycle and promotion, signed provenance and SBOMs, Xray policies, and GitHub Actions OIDC for passwordless CI/CD.

## What this service does
The Inventory service manages the book catalog, stock levels, and metadata. In the demo, it represents a typical Python microservice packaged both as a Python distribution and a Docker image.

## How this repo fits the demo
- Builds a Python package and Docker image in CI
- Generates SBOM and signs artifacts (placeholders in the initial scaffold)
- Publishes to Artifactory internal repositories mapped to project stages (DEV/QA/STAGING)
- Promotes artifacts through AppTrust stages via a manual workflow (QA → STAGING → PROD)
- Uses GitHub OIDC to authenticate to JFrog (no stored secrets)

## Repository layout
- `.github/workflows/ci.yml`: CI pipeline (test → build → SBOM/sign → publish)
- `.github/workflows/promote.yml`: Manual promotion workflow (with basic evidence placeholders)
- Application code, `Dockerfile`, and packaging files will be added as the demo evolves

## CI Expectations
The CI workflow expects these GitHub variables at the org or repo level:
- `PROJECT_KEY`: should be `bookverse`
- `JFROG_URL`: base URL of your JFrog instance
- `DOCKER_REGISTRY`: your Docker registry hostname configured in Artifactory

Internal repository targets follow this convention:
- Docker: `bookverse-inventory-docker-internal-local`
- Python: `bookverse-inventory-python-internal-local`

For production releases, images and packages should be published to:
- Docker: `bookverse-inventory-docker-release-local`
- Python: `bookverse-inventory-python-release-local`

## Promotion
Use the `Promote` workflow (`.github/workflows/promote.yml`) and select a target stage (QA, STAGING, PROD). The workflow includes evidence placeholders to illustrate gated promotion. In a full demo, these connect to test results, approvals, and change references.

## Related demo resources
- Demo plan and scope: see the BookVerse scenario overview in the AppTrust demo materials
- Other services: `bookverse-recommendations`, `bookverse-checkout`, `bookverse-platform`, and `bookverse-demo-assets`

---
This repository is intentionally minimal to focus on platform capabilities. Expand it with real application code or use as a scaffold for demonstrations.
