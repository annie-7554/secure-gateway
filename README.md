# 🔐 Secure Gateway — DevSecOps Pipeline

> A three-gate security pipeline with AI-powered advisory and policy-driven auto-remediation. Built to demonstrate shift-left security, sequential gate enforcement, and responsible AI automation boundaries.

---

## What This Project Does

Every pull request to `main` passes through three sequential security gates before code can be deployed. If any gate fails, subsequent gates do not run — vulnerable code never produces a container image, and no container image reaches production without human approval.

```
PR opened
    ↓
Gate 1 — Code Security       ← Semgrep SAST + TruffleHog + Snyk
    ↓ only if Gate 1 passes
Gate 2 — Container Security  ← Docker build + Trivy + SBOM
    ↓ only after merge + human trigger
Gate 3 — Secure Deploy       ← Environment approval + RBAC + audit trail
```

When Gate 1 fails, the **auto-remediation engine** triggers — classifying each finding and either applying a deterministic fix, posting a suggestion, or escalating to human review.

---

## Repository Structure

```
.
├── app/                        # Flask application
├── ai_agents/                  # AI advisory + remediation policy engine
│   ├── confidence_engine.py    # Remediation policy — what AI can/cannot fix
│   ├── security_advisor.py     # Claude API integration
│   ├── findings_parser.py      # SARIF parser
│   ├── llm_client.py           # Claude + OpenAI client with fallback
│   └── remediation_generator.py
├── scripts/
│   ├── auto_remediate.py       # Auto-remediation execution engine
│   └── analyze_findings.py     # AI advisor CLI for CI
├── tests/                      # 16 pytest tests
├── .semgrep/
│   └── rules.yml               # 9 custom security rules
├── .github/workflows/
│   ├── security.yml            # Gate 1 — Code Security
│   ├── build.yml               # Gate 2 — Container Security
│   ├── build-security.yml      # Gate 2 — Trivy + SBOM + cosign
│   ├── deploy.yml              # Gate 3 — Secure Deploy
│   ├── pr-security.yml         # PR-level scans + AI advisory comment
│   └── auto-remediate.yml      # Auto-remediation workflow
├── docker/Dockerfile           # Hardened container image
└── k8s/                        # Kubernetes manifests
```

---

## Gate 1 — Code Security

**Trigger:** `pull_request` to `main` AND `push` to `main`
**Workflow:** `.github/workflows/security.yml`

Three jobs run in parallel. All three must pass for `Gate 1 - Code Security Status` to succeed.

### SAST Analysis (Semgrep)

Runs 9 custom rules from `.semgrep/rules.yml` plus three public rulesets:

| Rule ID | Detects | Severity |
|---------|---------|----------|
| `py-sql-injection` | `DB.execute($QUERY)` without parameterization | ERROR |
| `py-eval-exec` | `eval()` / `exec()` usage | ERROR |
| `py-subprocess-shell` | `subprocess.*(shell=True)` | ERROR |
| `py-weak-hash` | `hashlib.md5()` / `hashlib.sha1()` | WARNING |
| `py-pickle-untrusted` | `pickle.load()` / `pickle.loads()` | ERROR |
| `hardcoded-secrets` | Variable names matching `password\|secret\|api_key\|token\|private_key` assigned string literals | ERROR |
| `py-unsafe-yaml-load` | `yaml.load($DATA)` without safe Loader | ERROR |
| `js-eval` | `eval($X)` in JavaScript/TypeScript | ERROR |
| `risky-templates` | `render_template($T, **$ARGS)` | WARNING |

Public rulesets: `p/security-audit`, `p/owasp-top-ten`, `p/cwe-top-25`

Findings counted via jq on SARIF output — suppressed findings (marked with `# nosemgrep`) are excluded from the count. The gate fails if any unsuppressed finding exists.

### Secret Scanning (TruffleHog)

Scans full git history from PR base SHA to HEAD. Fails on any pattern-matched credential (API keys, GitHub tokens, AWS keys, private keys). Findings logged to CI output.

### Dependency Vulnerability Scan (Snyk)

Scans `requirements.txt` against known CVE database. Fails on HIGH or CRITICAL severity findings. Skips gracefully if `SNYK_TOKEN` secret is not configured.

---

## Gate 2 — Container Security

**Trigger:** `workflow_run` watching Gate 1 — only runs when Gate 1 **succeeds**
**Workflow:** `.github/workflows/build.yml` + `build-security.yml`

This is the key sequential enforcement: Gate 2 uses `workflow_run` with `if: conclusion == 'success'` — if Gate 1 fails, Gate 2 never runs. Vulnerable code cannot produce a container image.

- Builds Docker image from `docker/Dockerfile` (non-root user, minimal base, pinned versions)
- Trivy scans image for HIGH/CRITICAL CVEs — fails build if found
- Syft generates SBOM in SPDX JSON format, uploaded as artifact (90-day retention)
- cosign signs the image if `COSIGN_PRIVATE_KEY` secret is configured
- SARIF uploaded to GitHub Security dashboard

---

## Gate 3 — Secure Deploy

**Trigger:** Manual `workflow_dispatch` only
**Workflow:** `.github/workflows/deploy.yml`

Requires a human to trigger. Environment approval gate configured in GitHub Environments for `production`. Full audit trail logged on every run: actor, commit SHA, environment, timestamp.

Runtime security enforced in Kubernetes:
- Non-root container (`runAsNonRoot: true`)
- Read-only filesystem (`readOnlyRootFilesystem: true`)
- No privilege escalation
- All Linux capabilities dropped
- Resource limits: CPU 500m, Memory 512Mi
- RBAC: least-privilege service account scoped to its own namespace

---

## AI Advisory Layer

**Trigger:** Every PR via `pr-security.yml`

When a PR opens or is updated, the AI advisor:
1. Parses the semgrep SARIF findings
2. Classifies risk (low / medium / high)
3. Posts a structured comment to the PR via GitHub API

The comment is **upserted** — on re-runs it updates the existing comment rather than creating a new one.

Uses Anthropic Claude Sonnet 4.6 via the Claude API. Falls back to OpenAI GPT-4o-mini if `ANTHROPIC_API_KEY` is not configured.

---

## Auto-Remediation Engine

**Trigger:** `workflow_run` watching Gate 1 — only fires when Gate 1 **fails** on a PR

### Policy Engine (`ai_agents/confidence_engine.py`)

Every finding is classified into one of three action tiers:

**AUTO_FIX** — deterministic, low blast radius, reversible:

| Rule | Code change applied |
|------|-------------------|
| `py-unsafe-yaml-load` | `yaml.load(` → `yaml.safe_load(` |
| `py-weak-hash` | `hashlib.md5/sha1(` → `hashlib.sha256(` |
| `hardcoded-secrets` | `VAR = "literal"` → `VAR = os.getenv("VAR")` + adds `import os` |

**SUGGEST** — fix is known but context-sensitive, inline suggestion posted, no code changed:
`py-subprocess-shell`, `py-eval-exec`, `py-pickle-untrusted`, `js-eval`, `risky-templates`

**ESCALATE** — human required, merge blocked, detailed guidance posted:
`py-sql-injection`, all unknown rule IDs (fail-safe default)

**Hard overrides (enforced in code, not configurable):**
- `CRITICAL` severity → always `ESCALATE` regardless of rule
- Category in `{authentication, authorization, business-logic, infrastructure, major-upgrade, zero-day, data-migration}` → always `ESCALATE`
- Unknown rule IDs → `ESCALATE` (default deny)

### Execution Engine (`scripts/auto_remediate.py`)

Three regex-based code fixers — applied only for AUTO_FIX findings:

```python
# yaml fix
re.sub(r'\byaml\.load\s*\(', 'yaml.safe_load(', src)

# weak hash fix
re.sub(r'\bhashlib\.(md5|sha1)\s*\(', 'hashlib.sha256(', src)

# hardcoded secret fix
re.sub(rf'\b{var}\s*=\s*["\'][^"\']*["\']', f'{var} = os.getenv("{var}")', src)
```

### Validation Loop

Every AUTO_FIX runs through three checks **before** a PR is opened:

```
1. pytest -q --tb=short           → unit tests must pass
2. semgrep --config .semgrep/rules.yml --error .  → rescan must show 0 findings
3. python -m py_compile **/*.py   → no syntax errors introduced
```

If any check fails → `git checkout .` reverts all changes → finding escalated to human.
If all pass → draft PR opened on branch `auto-fix/<base-branch>` → **requires developer approval before merge**.

### Secret Incident Response

When `hardcoded-secrets` fires, regardless of action tier:
1. Structured audit log written to CI output as `::error` annotation
2. Slack notification via `requests.post` to `SLACK_WEBHOOK_URL` (if configured)
3. Rotation guidance and incident details posted to PR comment

### PR Comment

Single upserted comment posted to the original failing PR:

```
## 🔧 Auto-Remediation Report

### ✅ Auto-fixed (HIGH confidence)
Draft PR opened. Validation: tests ✅ · rescan ✅ · syntax ✅
⚠️ Requires developer approval before merge.

### 💡 Suggestions (MEDIUM confidence)
Context-sensitive fixes for developer to apply manually.

### 🚨 Human Review Required (LOW confidence)
Business-logic or security-critical findings — AI remediation intentionally disabled.
```

### What AI Never Touches

```
Authentication logic     JWT, OAuth, MFA, session handling
Authorization / RBAC     permissions, roles, tenant isolation
SQL query logic          joins, transactions, ORM behavior
Infrastructure           IAM, firewall rules, K8s RBAC, VPC
Major dependency bumps   semver major, breaking API changes
Business logic flaws     race conditions, payment flows
Zero-day responses       no trusted remediation pattern exists
Database migrations      schema changes, encryption migration
```

> *"The pipeline intentionally restricts AI remediation to low-risk deterministic fixes to avoid unsafe modifications to business logic or security-critical infrastructure."*

---

## Attack Simulations

Three PRs demonstrate the gates working correctly:

| PR | Branch | Attack | Gate | Expected result |
|----|--------|--------|------|----------------|
| #4 | `gate1-sast-test` | SQL injection (`DB.execute($QUERY)`) | Gate 1 SAST | ❌ FAIL |
| #5 | `gate1-secret-test` | Hardcoded `API_TOKEN`, `PRIVATE_KEY` | Gate 1 SAST | ❌ FAIL |
| #6 | `gate2-vuln-dep-test` | `yaml.load()` without safe Loader | Gate 1 SAST | ❌ FAIL |

Clean PRs pass all gates. All three attack PRs have been verified to fail Gate 1 in CI.

---

## Quick Start

```bash
git clone https://github.com/annie-7554/secure-gateway.git
cd secure-gateway

python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run tests
pytest -q

# Run app
python app/app.py

# Run semgrep locally
semgrep --config .semgrep/rules.yml .
```

**Secrets to configure in GitHub repo settings:**

| Secret | Required for |
|--------|-------------|
| `ANTHROPIC_API_KEY` | AI advisory comments |
| `SNYK_TOKEN` | Dependency CVE scanning |
| `COSIGN_PRIVATE_KEY` | Image signing |
| `SLACK_WEBHOOK_URL` | Secret incident Slack alerts |

---

## Security Principles

- **Shift-Left** — SAST runs on every PR before merge
- **Sequential Gates** — Gate 2 cannot run if Gate 1 fails (`workflow_run`)
- **Defense-in-Depth** — code + container + deploy each have independent controls
- **Least Privilege** — service accounts, non-root containers, dropped capabilities
- **Fail-Safe Defaults** — unknown findings escalate to human, never auto-fixed
- **Human in the Loop** — auto-fix PRs are draft, Gate 3 requires manual trigger + approval
