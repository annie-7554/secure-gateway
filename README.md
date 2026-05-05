# 🔐 Secure DevSecOps CI/CD Pipeline

> A security-first CI/CD pipeline that prevents insecure code, vulnerable builds, and unsafe deployments from reaching production.

---

## 🌟 Highlights

- 🛡️ Enforces security at code, build, and deployment stages
- 🚫 Automatically blocks insecure changes before merge (when branch protection requires status checks)
- 🔍 Prevents vulnerable artifacts from being created
- 🔐 Controls deployments with approval + least privilege
- 🧪 Includes real attack simulations with remediation examples
- ⚡ Fast pipeline (approx. 5–8 minutes) with parallel checks — actual time depends on runner performance and network

---

## ℹ️ Overview

This repository implements a three-stage CI/CD security pipeline that validates software through its lifecycle using layered controls to:

- detect risks early
- stop insecure artifacts
- enforce safe deployments

---

## 🔧 Implementation (Tools Used)

The pipeline integrates standard security tooling to enforce controls at each stage:

- Semgrep for static analysis (SAST)
- TruffleHog for secret scanning
- Snyk for dependency vulnerability analysis (requires `SNYK_TOKEN` secret)
- Trivy for container image scanning
- Syft (via SBOM action) for SBOM generation
- Kyverno policy for image signature verification (requires Kyverno installed in cluster and Cosign public key configured)

---

## 🚀 Quick Start

Prerequisites:
- Docker
- Python 3.11+ and virtualenv
- git
- (Optional) Semgrep, Trivy installed for local scanning
- Configure GitHub secrets: `SNYK_TOKEN` for Snyk scans
- Configure a GitHub Environment (e.g., `production`) with required reviewers if you want approval gating

```bash
# Clone repository
git clone https://github.com/annie-7554/secure-gateway.git

# Navigate into project
cd secure-gateway

# Setup local environment (installs Python deps in venv)
bash scripts/setup.sh

# Run application (dev)
python src/app.py
```

Notes:
- `scripts/setup.sh` performs basic checks and builds a local image; it does not configure cluster-level components (Kyverno, Cosign keys, GitHub environment approvals).
- To enforce merge blocking you must enable branch protection rules in GitHub and require the workflow checks.

---

## 🛡️ Security Model

Gate 1 — Code Protection (Pre-Merge)
- Validates pull requests with Semgrep (SAST), TruffleHog (secrets), and Snyk (dependencies).
- Blocks merge if high/critical findings are present.

Gate 2 — Build Protection
- Builds container images using a hardened Dockerfile and scans with Trivy.
- Generates an SBOM for supply chain transparency.
- Fails the build on critical vulnerabilities.

Gate 3 — Deployment Protection
- Requires human approval via GitHub Environments for protected deployments.
- Enforces image signature verification via Kyverno admission policies (cluster must have Kyverno and Cosign public key configured).
- Enforces least-privilege runtime constraints via Kubernetes RBAC and pod securityContext.

---

## 🔁 Failure Modes (What Happens When Things Go Wrong)

- Secret exposure: credential accidentally committed → PR scan flags it and blocks merge; rotate secrets and remove from history.
- Vulnerable dependency: insecure package added → dependency scan flags and blocks merge or build; update or replace package.
- Insecure container: Trivy detects critical CVEs → build fails and image is not pushed/deployed.
- Unauthorized deployment: missing approval or unsigned image → deployment is denied by GitHub or Kyverno.

---

## 🧪 Attack Simulations

The `attack-simulations/` directory contains concrete examples for testing detection and remediation:
- SQL injection (Semgrep example)
- Hardcoded secret example (TruffleHog detection)
- Vulnerable dependency example (Snyk-related)
- Vulnerable container configuration (Trivy detection)

Each simulation includes explanation of where the issue is detected, why it fails, and how to fix it.

---

## ⚙️ Usage (Pipeline Flow)

- Pull Request → Code validation (Gate 1)
- Merge → Build & Container validation (Gate 2)
- Deployment → Approval & runtime verification (Gate 3)

---

## 📊 Pipeline Characteristics

- Execution time: ~5–8 minutes (approximate)
- Parallel checks for faster feedback
- Fail-fast on critical risks
- SARIF reports and SBOM artifacts uploaded to GitHub Actions

---

## 🔐 Security Principles

- Shift-Left Security — detect issues early
- Defense-in-Depth — multiple independent controls
- Least Privilege — minimal access permissions
- Fail-Safe Defaults — block unless explicitly allowed
- Secure Supply Chain — validate artifacts before deployment

---

## 🤝 Contributing

Contributions welcome. Recommended workflow:

```bash
git checkout -b feature/your-feature
git add <specific-files>
git commit -m "Add feature"
git push origin feature/your-feature
```

Please ensure:
- Do not commit secrets
- Do not use `git add .` indiscriminately
- All checks in GitHub Actions pass before opening a PR

