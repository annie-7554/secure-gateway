# Pipeline Architecture

## Sequential Gate Enforcement

The pipeline enforces strict sequential ordering. Each gate only runs if the previous gate passed.

```
Pull Request opened
        │
        ▼
┌───────────────────────────────────────────────────────┐
│  GATE 1 — Code Security                               │
│  Trigger: pull_request + push to main                 │
│                                                       │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │ SAST        │  │ Secrets      │  │ Dependencies│  │
│  │ Semgrep     │  │ TruffleHog   │  │ Snyk        │  │
│  │ 9 rules +   │  │ Full git     │  │ CVE scan    │  │
│  │ 3 rulesets  │  │ history      │  │ HIGH/CRIT   │  │
│  └─────────────┘  └──────────────┘  └─────────────┘  │
│           All 3 must pass → Gate 1 Status             │
└───────────────────────────────────────────────────────┘
        │
        │  workflow_run (only if Gate 1 conclusion == 'success')
        ▼
┌───────────────────────────────────────────────────────┐
│  GATE 2 — Container Security                          │
│  Trigger: workflow_run from Gate 1                    │
│                                                       │
│  Docker Build → Trivy Scan → SBOM → cosign sign      │
│  Fails on HIGH/CRITICAL CVEs in image                 │
└───────────────────────────────────────────────────────┘
        │
        │  Manual workflow_dispatch + human approval
        ▼
┌───────────────────────────────────────────────────────┐
│  GATE 3 — Secure Deploy                               │
│  Trigger: manual only                                 │
│                                                       │
│  Approval gate → kubectl apply → health checks        │
│  Audit trail logged: actor, SHA, env, timestamp       │
└───────────────────────────────────────────────────────┘
```

**Key enforcement:** Gate 2 uses `workflow_run` with `if: github.event.workflow_run.conclusion == 'success'`. If Gate 1 fails, Gate 2 is skipped — no container image is ever built from vulnerable code.

---

## Gate 1 — Code Security

**Workflow:** `.github/workflows/security.yml`
**Trigger:** `pull_request` to `main` AND `push` to `main`

Gate 1 runs on both PRs (catch before merge) and pushes to main (gate Gate 2). Three jobs run in parallel; a final `gate-1-status` job collects their results.

### Job 1: SAST Analysis

Tool: Semgrep
Output: `semgrep.sarif` → uploaded to GitHub Security dashboard

**Custom rules** (`.semgrep/rules.yml`):

| Rule ID | Pattern | Action |
|---------|---------|--------|
| `py-sql-injection` | `$DB.execute($QUERY)` without `$PARAMS` | Fail |
| `py-eval-exec` | `eval($X)` or `exec($X)` | Fail |
| `py-subprocess-shell` | `subprocess.*(shell=True)` | Fail |
| `py-weak-hash` | `hashlib.md5/sha1(...)` | Warn |
| `py-pickle-untrusted` | `pickle.load/loads($X)` | Fail |
| `hardcoded-secrets` | `$VAR = "..."` where VAR matches credential names | Fail |
| `py-unsafe-yaml-load` | `yaml.load($DATA)` single-argument call | Fail |
| `js-eval` | `eval($X)` in JS/TS | Fail |
| `risky-templates` | `render_template($T, **$ARGS)` | Warn |

**Public rulesets:** `p/security-audit`, `p/owasp-top-ten`, `p/cwe-top-25`

Finding count: parsed from SARIF via jq, excluding suppressed findings:
```bash
jq '[.runs[0].results[] | select(.suppressions == null or (.suppressions | length) == 0)] | length'
```
Gate fails if count > 0.

Note: `# nosemgrep` inline suppression excludes a finding from the count. Used only for intentional false positives (e.g., `host='0.0.0.0'` in containerised app, `TESTING=True` in test fixtures).

### Job 2: Secret Scanning

Tool: TruffleHog
Scans from `github.event.pull_request.base.sha` to `HEAD` — full history of the PR.
Fails on any pattern-matched credential regardless of whether it can be verified live.

### Job 3: Dependency Vulnerability Scan

Tool: Snyk
Threshold: `--severity-threshold=high --fail-on=all`
Requires `SNYK_TOKEN` secret. Skips gracefully if not configured — job still passes.

### gate-1-status

```yaml
needs: [semgrep-sast, secrets-scanning, dependency-scanning]
if: always()
```
Fails if any of the three jobs failed. This is the required status check that blocks PR merge.

---

## Gate 1 — AI Advisory

**Workflow:** `.github/workflows/pr-security.yml`
**Trigger:** `pull_request` — opened, synchronize, reopened

Runs in parallel with Gate 1. After scans complete, the `ai-advisor` job:
1. Parses `semgrep.sarif`
2. Calls Claude Sonnet 4.6 via Anthropic API (`ANTHROPIC_API_KEY`)
3. Falls back to OpenAI GPT-4o-mini if Claude unavailable
4. Produces a risk assessment: severity counts, key findings, recommended action
5. Upserts a single PR comment (updates existing bot comment, never duplicates)

The AI advisory is **non-blocking** — it posts information but does not control gate pass/fail.

---

## Gate 1 — Auto-Remediation

**Workflow:** `.github/workflows/auto-remediate.yml`
**Trigger:** `workflow_run` watching Gate 1 — only when `conclusion == 'failure'` AND `event == 'pull_request'`

Only fires on failing PRs. Never runs on clean code or direct pushes to main.

### Policy Engine (`ai_agents/confidence_engine.py`)

Maps each finding to one of three action tiers:

#### AUTO_FIX tier
Deterministic 1:1 replacements. Safe to automate because the fix pattern is unambiguous regardless of surrounding business logic.

| Rule | Fix applied |
|------|-------------|
| `py-unsafe-yaml-load` | `re.sub(r'\byaml\.load\s*\(', 'yaml.safe_load(', src)` |
| `py-weak-hash` | `re.sub(r'\bhashlib\.(md5\|sha1)\s*\(', 'hashlib.sha256(', src)` |
| `hardcoded-secrets` | `re.sub(rf'\b{var}\s*=\s*["\'][^"\']*["\']', f'{var} = os.getenv("{var}")', src)` |

#### SUGGEST tier
Fix is known but context-sensitive. The engine posts a precise suggestion to the PR — no code changes.

| Rule | Why not auto-fixed |
|------|--------------------|
| `py-subprocess-shell` | Removing `shell=True` requires understanding the command — wrong list-form args silently change behavior |
| `py-eval-exec` | `ast.literal_eval` is not always a valid replacement |
| `py-pickle-untrusted` | json/msgpack are not always wire-compatible |
| `js-eval` | Depends on what is being evaluated |
| `risky-templates` | Sanitization strategy depends on data shape |

#### ESCALATE tier
Human review required. Merge is blocked. Detailed guidance posted.

| Rule / Condition | Reason |
|-----------------|--------|
| `py-sql-injection` | Fix requires understanding query structure, joins, transactions, ORM |
| `CRITICAL` severity | Blast radius of a wrong fix outweighs automation benefit |
| Category: `authentication` | JWT, OAuth, MFA — security-critical, never automated |
| Category: `authorization` | RBAC, permissions — privilege escalation risk |
| Category: `infrastructure` | IAM, firewall, K8s — outage/exposure risk |
| Category: `business-logic` | Race conditions, payment flows — app context required |
| Category: `zero-day` | No trusted remediation pattern exists |
| Unknown rule IDs | Fail-safe default — AI does not guess |

### Validation Loop

Every AUTO_FIX runs three checks before a PR is opened:

```
Step 1: pytest -q --tb=short
         Unit tests must pass. Catches behavioral regressions.

Step 2: semgrep --config .semgrep/rules.yml --error .
         Rescan confirms the finding is actually resolved.
         Catches cases where regex fixed one instance but missed others.

Step 3: python -m py_compile on all .py files
         Confirms fix did not produce invalid syntax.
```

On failure: `git checkout .` reverts all changes → finding escalated to ESCALATE tier.
On success: draft PR opened on branch `auto-fix/<base-branch>`.

**Draft PRs require developer approval before merge.** Gate 1 re-runs on the auto-fix PR as a final independent check.

### Secret Incident Response

When `hardcoded-secrets` fires (regardless of other action):
1. `::error` annotation written to CI output with structured JSON audit log
2. `requests.post` to `SLACK_WEBHOOK_URL` (if env var configured) with alert message
3. Rotation guidance posted to PR comment

---

## Gate 2 — Container Security

**Workflow:** `.github/workflows/build.yml` + `build-security.yml`
**Trigger:** `workflow_run` from Gate 1 with `conclusion == 'success'`

### build.yml (Gate 2 main)

1. Checkout at `github.sha`
2. Build: `docker build -t devsecops-app:$SHA -f docker/Dockerfile .`
3. Trivy scan: `--severity HIGH,CRITICAL --format sarif`
4. Fail if SARIF contains any results
5. SBOM: `anchore/sbom-action` in SPDX JSON format, retained 90 days
6. SARIF uploaded to GitHub Security tab

### build-security.yml (supplemental)

Trivy scan with separate configuration, SARIF to GitHub Security.
cosign image signing if `COSIGN_PRIVATE_KEY` configured.
Push to GHCR if signing succeeds.

### Dockerfile security (`docker/Dockerfile`)

- Base: `python:3.11-slim` (minimal attack surface)
- Non-root user: `appuser:1000`
- No unnecessary packages installed
- Health check configured for orchestration readiness

### Container remediation policy

Auto-fix is **not applied** at Gate 2. Reason: bumping a base image digest requires rebuilding and retesting the container. An automated Dockerfile commit could silently change runtime behavior. Pattern: SUGGEST + human review + Gate 2 re-runs after Dockerfile update.

---

## Gate 3 — Secure Deploy

**Workflow:** `.github/workflows/deploy.yml`
**Trigger:** `workflow_dispatch` only (human must initiate)

```yaml
environment:
  name: ${{ inputs.environment }}   # staging or production
```

GitHub Environments require approval from designated reviewers before the job proceeds.

Audit trail logged on every run:
```
Actor:       $DEPLOY_ACTOR
Environment: $DEPLOY_ENV
Commit:      $DEPLOY_SHA
Timestamp:   $(date -u +'%Y-%m-%dT%H:%M:%SZ')
```

All environment values passed via `env:` block — never interpolated directly into `run:` to prevent shell injection.

Kubernetes runtime security (documented in `k8s/`):
- `runAsNonRoot: true`
- `readOnlyRootFilesystem: true`
- `allowPrivilegeEscalation: false`
- `capabilities: drop: ["ALL"]`
- Resource limits: CPU 500m, Memory 512Mi
- RBAC: service account scoped to its own namespace

---

## Attack Simulation Results

| PR | Attack | Rule triggered | Gate result |
|----|--------|---------------|-------------|
| #4 | SQL injection | `py-sql-injection` | Gate 1 SAST ❌ FAIL |
| #5 | Hardcoded secrets | `hardcoded-secrets` | Gate 1 SAST ❌ FAIL |
| #6 | Unsafe yaml.load() | `py-unsafe-yaml-load` | Gate 1 SAST ❌ FAIL |
| Clean | No vulnerabilities | — | All gates ✅ PASS |

All three attack branches fail Gate 1. Gate 2 is never reached for any of them.

---

## Workflow Dependency Map

```
pull_request → security.yml (Gate 1)
             → pr-security.yml (AI advisory + PR-level scans)

push to main → security.yml (Gate 1 — gates Gate 2)

Gate 1 success on main → build.yml (Gate 2)
                       → build-security.yml (Gate 2)

Gate 1 failure on PR → auto-remediate.yml

workflow_dispatch → deploy.yml (Gate 3)
```

---

## Tools Reference

| Gate | Tool | Purpose | Failure condition |
|------|------|---------|------------------|
| 1 | Semgrep | SAST — 9 custom + 3 public rulesets | Any unsuppressed finding |
| 1 | TruffleHog | Secret scanning — full git history | Any pattern match |
| 1 | Snyk | Dependency CVEs | HIGH or CRITICAL severity |
| 1 | Claude Sonnet 4.6 | AI advisory — non-blocking | n/a |
| 2 | Trivy | Container CVE scan | HIGH or CRITICAL in image |
| 2 | Syft/SBOM Action | SBOM generation — SPDX JSON | n/a (artifact only) |
| 2 | cosign | Image signing | n/a (skips if no key) |
| 3 | GitHub Environments | Human approval gate | Approval not granted |
| 3 | Kubernetes | Runtime security | Health check failure |

---

## Design Decisions

**SARIF over exit codes** — Semgrep v1.162 exits 0 in SARIF mode even when findings exist. The `--error` flag is unreliable. Findings are counted via jq on the SARIF output with suppression filtering.

**workflow_run over push trigger** — Gate 2 is causally dependent on Gate 1 success, not just temporally coincidental. A push trigger would allow Gate 2 to run even after a Gate 1 failure.

**metavariable-regex for secrets** — `pattern-regex` cannot inspect identifier names. `metavariable-regex` matches the variable name itself (`API_TOKEN`, `PRIVATE_KEY`) which is what determines whether an assignment is a hardcoded credential.

**Upsert PR comments** — The bot was posting a new Security Advisory comment on every CI re-run. `listComments` → `updateComment` (or `createComment`) ensures one comment per PR, always current.

**Draft PRs for auto-fix** — Auto-fix PRs are opened as drafts and require developer approval. Gate 1 re-runs on the auto-fix branch as a final check. Automation never merges to main without human sign-off.

**ESCALATE as default** — Unknown rule IDs fail safe to human escalation. The policy engine defaults to denying automation, not allowing it.
