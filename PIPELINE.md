# DevSecOps Pipeline Architecture

## Overview

Three-stage security pipeline implementing comprehensive vulnerability detection and enforcement across code, container, and deployment artifacts.

## Architecture

```
Code Push → Gate 1: Code Security → Gate 2: Container Security → Gate 3: Deployment
               ↓                          ↓                            ↓
         Semgrep SAST            Docker Build + Trivy         Approval + K8s RBAC
         TruffleHog              SBOM Generation              Image Signature Verification
         Snyk Dependencies       CVE Scanning                 Policy Enforcement
```

## Gate 1: Code Security

**Trigger:** Pull requests to main

**Controls:**
- **Semgrep SAST**: Pattern-based vulnerability detection (OWASP Top 10, CWE Top 25)
  - Detects: SQL injection, XSS, weak crypto, insecure deserialization
  - Configuration: p/security-audit, p/owasp-top-ten, p/cwe-top-25

- **TruffleHog**: Credential scanning across repository history
  - Detects: AWS keys, API tokens, private keys, database credentials
  - Mode: Verified findings only (cross-references against leaked credential databases)

- **Snyk**: Dependency vulnerability scanning
  - Scans: requirements.txt, package.json, pom.xml
  - Severity threshold: HIGH and CRITICAL
  - Provides remediation guidance and upgrade paths

**Failure Criteria:**
- Any HIGH/CRITICAL Semgrep findings
- Any verified secret in commit history
- Any HIGH/CRITICAL CVE in dependencies

**Output:**
- SARIF reports in GitHub Security tab
- Clear remediation guidance
- Block PR merge until resolved

## Gate 2: Build & Container

**Trigger:** Merge to main

**Controls:**
- **Secure Dockerfile**
  - Non-root user execution (appuser:1000)
  - Minimal base image (python:3.11-slim)
  - Pinned package versions for reproducibility
  - Health checks for orchestration
  - Multi-stage build with dependency caching

- **Trivy Container Scanning**
  - Scans: OS packages, language dependencies, configuration files
  - Database: NVD + Alpine/Debian security advisories
  - Generates: SARIF for integration with GitHub Security

- **SBOM Generation**
  - Tool: Syft (from Anchore)
  - Format: SPDX JSON
  - Use cases: Incident response, license compliance, supply chain transparency

**Failure Criteria:**
- Any CRITICAL vulnerability in base image or dependencies
- Build script validation fails

**Output:**
- Container image pushed to registry
- SBOM artifact stored for audit
- SARIF report in GitHub

## Gate 3: Deployment

**Trigger:** Manual workflow dispatch

**Controls:**
- **Environment Protection**: GitHub environment approval required
  - Requires: Authorized reviewer approval
  - Audit trail: All deployments logged with approver identity

- **Image Signature Verification**: Kyverno admission controller
  - Policy: verifyImageSignature
  - Effect: Reject unsigned images at admission time
  - Keys: Public key stored in kyverno namespace

- **Kubernetes RBAC**
  - Service account: devsecops-app (limited permissions)
  - Role: Read-only access to pods in devsecops-app namespace
  - Effect: Container escape cannot escalate to cluster control

- **Pod Security**
  - runAsNonRoot: true
  - readOnlyRootFilesystem: true (with tmpfs for /tmp)
  - allowPrivilegeEscalation: false
  - securityContext capabilities: ALL dropped
  - Resource limits: CPU 500m, Memory 512Mi

**Output:**
- Deployment audit log
- Pod running with enforced security context
- Health checks passing (readiness/liveness probes)

## Security Principles

### Shift-Left Security
Vulnerabilities detected as early as possible in development (code review → build → deployment)

### Defense-in-Depth
Multiple independent gates catch different attack vectors:
- Logic vulnerabilities (Gate 1)
- Supply chain attacks (Gate 1, 2)
- Vulnerable packages (Gate 2)
- Malicious images (Gate 3)

### Least Privilege
- Service accounts have minimal necessary permissions
- Non-root container processes
- Read-only filesystems where possible
- Capabilities explicitly dropped

### Supply Chain Security
- SBOM generation for dependency tracking
- Image signature verification for origin authenticity
- Dependency scanning for known vulnerabilities
- Reproducible builds with pinned versions

### Auditability
- Approval gate creates immutable record
- GitHub Actions logs all scanning activities
- Kyverno logs policy violations
- Image signatures provide non-repudiation

## Tools & Justification

| Gate | Tool | Capability | Rationale |
|------|------|-----------|-----------|
| 1 | Semgrep | SAST | Excellent rule quality, open-source, local execution |
| 1 | TruffleHog | Secret Scanning | Industry standard, verified findings mode |
| 1 | Snyk | Dependency Scanning | Comprehensive CVE database, clear remediation |
| 2 | Trivy | Container Scanning | Maintained by Aqua, fast, SARIF support |
| 2 | Syft | SBOM Generation | Comprehensive, standard formats (SPDX/CycloneDX) |
| 3 | Kyverno | Policy Enforcement | Kubernetes-native, YAML policies, signature verification |

## Performance

- Gate 1: ~2-3 minutes (parallel scans)
- Gate 2: ~2-3 minutes (build + scan)
- Gate 3: ~1-2 minutes (deployment + validation)
- **Total pipeline:** ~5-8 minutes

## Integration Points

- GitHub Actions for orchestration
- GitHub Security tab for findings visualization
- GitHub Environments for approval gates
- Kubernetes for runtime security enforcement
- Container registry for image storage and scanning

## Future Enhancements

- Cosign for image signing (supply chain provenance)
- Vault/Secrets Manager for credential management
- Prometheus/CloudWatch for pipeline metrics
- ArgoCD for GitOps-driven deployments
- Network policies for pod-to-pod communication controls
