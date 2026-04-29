# Architecture

Secure Gateway demonstrates a three-gate DevSecOps pipeline:

- Gate 1 (PR Security): Semgrep for SAST, TruffleHog for secret scanning, OWASP Dependency-Check for dependency CVEs.
- Gate 2 (Build/Supply Chain): Docker build, Trivy image scanning, SBOM generation (Syft), image signing with Cosign, image pushed to GHCR.
- Gate 3 (Deployment Authorization): GitHub environment approval + deploy workflow, Kubernetes RBAC and Kyverno admission policy to verify Cosign signatures.

Components:
- app/: Flask application containerized by Docker.
- .github/workflows/: GitHub Actions workflows implementing the gates.
- k8s/: Kubernetes manifests for deployment, service, namespace, and RBAC.
- kyverno/: Kyverno policy to verify image signatures.
- docs/: Documentation and demo materials.
