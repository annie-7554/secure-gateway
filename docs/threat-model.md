# Threat Model

Threats covered by this pipeline:

- Vulnerable code merged via PRs — mitigated by Semgrep rules and PR gating.
- Leaked secrets in commits/history — mitigated by TruffleHog git-history scanning.
- Vulnerable dependencies — mitigated by OWASP Dependency-Check.
- Vulnerable container images — mitigated by Trivy image scanning and SBOM checks.
- Tampered/unsigned images — mitigated by Cosign signing and Kyverno verification.
- Unauthorized deployments — mitigated by GitHub environment approvals and Kubernetes RBAC.

Assumptions and limitations:
- This demo uses GitHub Actions and GHCR; secrets must be stored in repository secrets.
- Kyverno policy requires the public key to be provided in the policy or via cluster config.
