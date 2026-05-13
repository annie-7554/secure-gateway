# Complete Pipeline Reference
## Everything that happens from PR to Production

---

## Full Flow Overview

```
Developer pushes code
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Pull Request opened against main                                   │
│                                                                     │
│  ┌──────────────────────┐    ┌──────────────────────────────────┐   │
│  │  security.yml        │    │  pr-security.yml                 │   │
│  │  Gate 1 - Code       │    │  PR Security Gate                │   │
│  │  Security            │    │  (runs in parallel)              │   │
│  │                      │    │                                  │   │
│  │  ┌────────────────┐  │    │  ┌──────┐ ┌──────┐ ┌────────┐   │   │
│  │  │ SAST (Semgrep) │  │    │  │Tests │ │Sgrep │ │Truffle │   │   │
│  │  │ Secrets        │  │    │  │pytest│ │rules │ │Hog     │   │   │
│  │  │ (TruffleHog)   │  │    │  └──────┘ └──────┘ └────────┘   │   │
│  │  │ Dependencies   │  │    │  ┌──────────────────────────┐    │   │
│  │  │ (Snyk)         │  │    │  │ OWASP Dependency Check   │    │   │
│  │  └────────────────┘  │    │  └──────────────────────────┘    │   │
│  │  gate-1-status ✅/❌  │    │  AI Advisor → PR comment        │   │
│  └──────────────────────┘    └──────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
         │
         ├── Gate 1 FAILED ──────────────────────────────────────────┐
         │                                                            │
         │                              auto-remediate.yml           │
         │                              ┌────────────────────────┐   │
         │                              │ Download semgrep SARIF │   │
         │                              │ Classify each finding  │   │
         │                              │ AUTO_FIX / SUGGEST /   │   │
         │                              │ ESCALATE               │   │
         │                              │ Validate fixes         │   │
         │                              │ Open draft PR / post   │   │
         │                              │ comment on original PR │   │
         │                              └────────────────────────┘   │
         │                                                            │
         ├── Gate 1 PASSED ─────────────────────────────────────────▶│
         │         │                                                  │
         │   Merge to main                                            │
         │         │                                                  │
         ▼         ▼                                                  │
┌──────────────────────────────────────────────────────────────────┐  │
│  Gate 1 runs AGAIN on push to main (gates Gate 2)               │  │
│  security.yml — push trigger                                     │  │
└──────────────────────────────────────────────────────────────────┘  │
         │                                                            │
         ├── Gate 1 FAILED on main ──── Gate 2 SKIPPED               │
         │                                                            │
         ├── Gate 1 PASSED on main                                   │
         │         │                                                  │
         ▼         ▼                                                  │
┌──────────────────────────────────────────────────────────────────┐  │
│  build.yml + build-security.yml                                  │  │
│  Gate 2 — Container Security                                     │  │
│  Trigger: workflow_run (Gate 1 success only)                     │  │
│                                                                  │  │
│  Docker build → Trivy scan → SBOM → cosign sign → push GHCR     │  │
│  AI Advisor runs on Gate 2 findings                              │  │
│  BUILD FAILS if HIGH/CRITICAL CVE found                          │  │
└──────────────────────────────────────────────────────────────────┘  │
         │                                                            │
         │  Human manually triggers                                   │
         ▼                                                            │
┌──────────────────────────────────────────────────────────────────┐  │
│  deploy.yml                                                      │  │
│  Gate 3 — Secure Deploy                                          │  │
│  Trigger: workflow_dispatch (human only)                         │  │
│                                                                  │  │
│  GitHub Environment approval → kubectl apply → health checks     │  │
│  Full audit trail logged                                         │  │
│  AI Advisor runs on deployment context                           │  │
└──────────────────────────────────────────────────────────────────┘  │
```

---

## Workflow 1 — `security.yml` (Gate 1 - Code Security)

**Trigger:** `pull_request` to main AND `push` to main
**Purpose:** Scans code for vulnerabilities before merge AND before Gate 2 runs

### Jobs (all run in parallel)

**Job: `semgrep-sast` (SAST Analysis)**
```
1. Checkout code
2. pip install semgrep
3. Run semgrep with:
   - .semgrep/rules.yml       (9 custom rules)
   - p/security-audit         (public ruleset)
   - p/owasp-top-ten          (public ruleset)
   - p/cwe-top-25             (public ruleset)
   Output: semgrep.sarif
4. Upload SARIF to GitHub Security tab
5. Count unsuppressed findings via jq:
   jq '[.runs[0].results[] | select(.suppressions == null or
       (.suppressions | length) == 0)] | length' semgrep.sarif
6. FAIL if count > 0
```

**Job: `secrets-scanning` (Secret Scanning)**
```
1. Checkout with fetch-depth: 0 (full git history)
2. TruffleHog scans from PR base SHA to HEAD
3. extra_args: --debug (no --only-verified — catches pattern matches too)
4. FAIL if any credential pattern found
```

**Job: `dependency-scanning` (Dependency Vulnerability Scan)**
```
1. Check if SNYK_TOKEN secret exists
2. If YES: Run Snyk with --severity-threshold=high --fail-on=all
3. If NO:  Skip gracefully, job still passes
```

**Job: `gate-1-status` (Gate 1 - Code Security Status)**
```
needs: [semgrep-sast, secrets-scanning, dependency-scanning]
if: always()

Checks all three results. FAIL if any != 'success'.
This is the required status check that blocks PR merge.
```

---

## Workflow 2 — `pr-security.yml` (PR Security Gate)

**Trigger:** `pull_request` — opened, synchronize, reopened
**Purpose:** Additional PR-level scans + AI advisory comment
**Runs in parallel with security.yml — does NOT block Gate 1**

### Jobs (all run in parallel except ai-advisor)

**Job: `tests`**
```
1. pip install -r requirements.txt pytest
2. pytest -q
3. FAIL if any test fails
```

**Job: `semgrep`**
```
1. pip install semgrep
2. semgrep --config .semgrep/rules.yml (custom rules only)
3. Upload SARIF artifact (used by ai-advisor)
4. FAIL if unsuppressed findings found
```

**Job: `trufflehog`**
```
1. pip install trufflehog
2. trufflehog git --json . > trufflehog.json
3. FAIL if trufflehog.json has findings
```

**Job: `dependency-check`**
```
1. docker run owasp/dependency-check --scan . --format SARIF
2. Upload SARIF to GitHub Security tab
3. continue-on-error: true (NVD API rate limiting issues)
```

**Job: `ai-advisor`** (runs after semgrep, trufflehog, dependency-check)
```
needs: [semgrep, trufflehog, dependency-check]
if: always()

1. pip install -r requirements.txt
2. Download semgrep-sarif artifact
3. python3 scripts/analyze_findings.py
      --semgrep-sarif semgrep.sarif
      --gate gate1
      --pr-number <PR number>
      --output-comment pr-comment.md
   → Calls Claude Sonnet 4.6 (ANTHROPIC_API_KEY)
   → Falls back to OpenAI GPT-4o-mini if unavailable
   → Writes risk assessment to pr-comment.md

4. Post PR comment (upsert — update existing bot comment or create new):
   - Find existing comment with '🤖 **Security Advisory**'
   - If found: updateComment
   - If not found: createComment
```

**What the AI advisor comment looks like:**
```
🤖 Security Advisory
Risk Assessment: low/medium/high
Gate Status: Gate 1
Summary: Found N severity findings.
Key Findings: [MEDIUM] semgrep.py-sql-injection
Recommended Action: review and fix as scheduled
```

---

## Workflow 3 — `auto-remediate.yml` (Auto Remediation)

**Trigger:** `workflow_run` watching "Gate 1 - Code Security"
**Condition:** `conclusion == 'failure'` AND `event == 'pull_request'`
**Purpose:** Triage findings and apply fixes, suggest, or escalate

### What fires this workflow
Only when Gate 1 fails on a PR. Never fires on:
- Clean PRs (Gate 1 passes)
- Direct pushes to main
- Manual triggers

### Job: `triage`

```
1. Checkout PR head SHA
2. pip install requirements + semgrep + pytest
3. Download semgrep-sarif artifact from failed Gate 1 run
4. python3 scripts/auto_remediate.py
      --sarif semgrep.sarif
      --pr-number <number>
      --base-branch <branch>
      --repo-root .
```

### Policy Engine (`ai_agents/confidence_engine.py`)

Every finding is looked up by rule ID and severity:

**AUTO_FIX** — code is modified, validated, draft PR opened:

| Rule | Fix applied |
|------|-------------|
| `py-unsafe-yaml-load` | `re.sub(r'\byaml\.load\s*\(', 'yaml.safe_load(', src)` |
| `py-weak-hash` | `re.sub(r'\bhashlib\.(md5\|sha1)\s*\(', 'hashlib.sha256(', src)` |
| `hardcoded-secrets` | `re.sub(rf'\b{var}\s*=\s*["\'][^"\']*["\']', f'{var} = os.getenv("{var}")', src)` + `import os` added if missing |

**SUGGEST** — text suggestion posted, zero code changes:

| Rule | Why not auto-fixed |
|------|--------------------|
| `py-subprocess-shell` | Wrong list-form args silently change behavior |
| `py-eval-exec` | `ast.literal_eval` not always a valid replacement |
| `py-pickle-untrusted` | json/msgpack not always wire-compatible |
| `js-eval` | Depends on what is being evaluated |
| `risky-templates` | Sanitization strategy depends on data shape |

**ESCALATE** — human required, detailed guidance posted:

| Condition | Reason |
|-----------|--------|
| `py-sql-injection` | Requires understanding query structure, joins, transactions |
| `CRITICAL` severity | Any rule — blast radius too high for automation |
| Category `authentication` | JWT, OAuth, MFA — never automated |
| Category `authorization` | RBAC, permissions — privilege escalation risk |
| Category `infrastructure` | IAM, firewall — outage risk |
| Category `business-logic` | Race conditions, payment flows — app context required |
| Category `zero-day` | No trusted remediation pattern exists |
| Unknown rule ID | Fail-safe default — AI does not guess |

### Validation loop (AUTO_FIX only)

```
After applying regex fix:

Step 1: pytest -q --tb=short
         → behavioral regressions caught

Step 2: semgrep --config .semgrep/rules.yml --error .
         → confirms finding is actually gone

Step 3: python -m py_compile on all .py files
         → confirms no syntax errors introduced

If ANY step fails:
  → git checkout . (revert everything)
  → finding promoted to ESCALATE
  → ::error annotation written to CI
  → human escalation comment posted

If ALL steps pass:
  → git checkout -b auto-fix/<base-branch>
  → git commit + git push
  → gh pr create --draft
  → Draft PR requires developer approval before merge
  → Gate 1 re-runs on the auto-fix branch
```

### Secret incident response

When `hardcoded-secrets` fires (in addition to AUTO_FIX):
```
1. Structured JSON audit log → CI ::error annotation:
   {
     "event": "SECRET_EXPOSURE_DETECTED",
     "severity": "CRITICAL",
     "pr": <number>,
     "rule": "hardcoded-secrets",
     "file": "<affected file>",
     "action_required": [
       "Rotate the exposed credential immediately",
       "Check cloud provider logs for unauthorized access",
       "Remove secret from git history (BFG Repo-Cleaner)",
       "Review who had access to this branch"
     ]
   }

2. Slack POST (if SLACK_WEBHOOK_URL configured):
   requests.post(webhook, json={
     "text": ":rotating_light: Secret exposure detected in PR #N ..."
   }, timeout=5)
```

### Remediation PR comment (upserted on every run)

```
## 🔧 Auto-Remediation Report

### ✅ Auto-fixed (N — HIGH confidence)
Draft PR opened. Validation: tests ✅ · rescan ✅ · syntax ✅
⚠️ Requires developer approval before merging.

### 💡 Suggestions (N — MEDIUM confidence)
- `py-subprocess-shell` in scripts/deploy.sh
  Replace shell=True with list args...

### 🚨 Human Review Required (N — LOW confidence)
- `py-sql-injection` in app/queries.py
  Reason: business logic context required
  Guidance: Use cursor.execute(query, (param,))...
```

---

## Workflow 4 — `build.yml` (Gate 2 - Build & Container Security)

**Trigger:** `workflow_run` from "Gate 1 - Code Security"
**Condition:** `conclusion == 'success'` AND branch == main
**Purpose:** Build and scan container image — only after Gate 1 passes

```
Job: build-and-scan
if: workflow_dispatch OR workflow_run.conclusion == 'success'

1. Checkout at github.sha
2. docker build -t devsecops-app:$SHA -f docker/Dockerfile .
3. Trivy scan (aquasecurity/trivy-action):
   - severity: HIGH,CRITICAL
   - format: sarif
   - output: trivy-results.sarif
4. Upload SARIF to GitHub Security tab
5. syft SBOM generation (anchore/sbom-action):
   - format: spdx-json
   - output: sbom.spdx.json
   - artifact retained 90 days
6. Count SARIF results:
   VULN_COUNT=$(jq '.runs[0].results | length' trivy-results.sarif)
   FAIL if VULN_COUNT > 0
7. Gate 2 Summary logged
```

**If Trivy finds HIGH/CRITICAL CVE:**
- Build fails
- SARIF visible in GitHub Security tab
- No notification, no auto-fix, no suggestion
- Human must update Dockerfile base image digest and re-trigger

---

## Workflow 5 — `build-security.yml` (Build Security Gate)

**Trigger:** `workflow_run` from "Gate 1 - Code Security"
**Condition:** `conclusion == 'success'`
**Purpose:** Supplemental build — Trivy via CLI + cosign signing + GHCR push

```
Job: build
if: workflow_run.conclusion == 'success'

1. docker build -t ghcr.io/<repo>/secure-gateway:$SHA .
2. Install Trivy via install script
3. trivy image --format sarif --severity CRITICAL,HIGH --exit-code 1
   → TRIVY_RC captured
4. Upload Trivy SARIF to GitHub Security tab
5. Upload trivy SARIF as artifact
6. FAIL if TRIVY_RC != 0
7. syft SBOM: cyclonedx-json format → sbom.json
8. cosign image signing (if COSIGN_PRIVATE_KEY configured):
   - Write key to cosign.key (chmod 600)
   - cosign sign --key cosign.key <image>
   - Skip gracefully if no key
9. docker push to ghcr.io (latest tag)

Job: ai-advisor (after build, if: always())
1. Download trivy SARIF artifact
2. python3 scripts/analyze_findings.py
      --trivy-sarif trivy-scan/trivy-report.sarif
      --gate gate2
      --output-summary advisor-summary.json
   → Claude analyzes container findings
   → Produces advisor-summary.json artifact
```

---

## Workflow 6 — `deploy.yml` (Gate 3 - Secure Deployment)

**Trigger:** `workflow_dispatch` — human must manually trigger
**Inputs:** `environment` (staging | production)
**Purpose:** Human-approved deployment with full audit trail

```
Job: deploy
environment: ${{ inputs.environment }}
  → GitHub Environment approval gate — designated reviewer must approve

permissions:
  contents: read
  id-token: write   (for OIDC token)

Steps:
1. Log audit trail (all values from env: block, no direct interpolation):
   Actor:       $DEPLOY_ACTOR
   Environment: $DEPLOY_ENV
   Commit:      $DEPLOY_SHA
   Timestamp:   $(date -u +'%Y-%m-%dT%H:%M:%SZ')

2. Setup kubeconfig (OIDC token or service account secret)

3. kubectl apply -f k8s/
   Enforces:
   - RBAC: least-privilege service account
   - Pod security: non-root, read-only filesystem
   - No privilege escalation
   - All capabilities dropped
   - Resource limits: CPU 500m, Memory 512Mi

4. Health check verification:
   - Pod ready replicas == desired replicas
   - Readiness probe passing
   - /health endpoint responding

5. On success: log completion with timestamp
6. On failure: exit 1

Job: ai-advisor-deployment (after deploy, if: always())
1. python3 scripts/analyze_findings.py --gate gate3
   → Claude generates deployment context summary
   → Uploaded as deployment-context.md artifact
```

---

## AI Agents (`ai_agents/`)

### `llm_client.py`
Handles all LLM communication.
- Primary: Anthropic Claude Sonnet 4.6 via `anthropic` SDK
- Fallback: OpenAI GPT-4o-mini via `openai` SDK
- Falls back automatically if `ANTHROPIC_API_KEY` not set

### `findings_parser.py`
Parses SARIF files into `Finding` objects with rule ID, severity, file, message.

### `security_advisor.py`
Main advisory class. Takes findings, calls LLM, returns risk assessment with:
- Overall risk level (low / medium / high)
- Finding count by severity
- Recommended action

### `confidence_engine.py`
Remediation policy engine. Maps rule ID + severity → `Action` enum:
- `AUTO_FIX` — 3 rules
- `SUGGEST` — 5 rules
- `ESCALATE` — 1 explicit + catch-all

Hard overrides:
- CRITICAL severity → always ESCALATE
- 7 category strings → always ESCALATE

### `remediation_generator.py`
Generates human-readable remediation guidance using LLM.
Falls back to hardcoded severity-based guidance if LLM unavailable.

### `advisor_prompts.py`
System prompts and prompt templates for the LLM calls.

---

## Scripts (`scripts/`)

### `analyze_findings.py`
CLI used by all three gate workflows.
```
--semgrep-sarif   SARIF from semgrep scan
--trivy-sarif     SARIF from Trivy scan
--gate            gate1 | gate2 | gate3
--pr-number       PR number for comment posting
--output-comment  write advisory comment to file
--output-summary  write JSON summary to file
```
Writes `$GITHUB_OUTPUT` (not deprecated `::set-output`).

### `auto_remediate.py`
Auto-remediation execution engine.
```
--sarif       semgrep SARIF to triage
--pr-number   PR to post comments on
--base-branch branch the PR targets
--repo-root   repo directory
--dry-run     plan but don't apply
```
Exits 0 (success), 1 (unexpected error), 2 (validation failed).

---

## Custom Semgrep Rules (`.semgrep/rules.yml`)

| Rule ID | Pattern | Severity | Action tier |
|---------|---------|----------|-------------|
| `py-sql-injection` | `$DB.execute($QUERY)` without params | ERROR | ESCALATE |
| `py-eval-exec` | `eval($X)` or `exec($X)` | ERROR | SUGGEST |
| `py-subprocess-shell` | `subprocess.*(shell=True)` | ERROR | SUGGEST |
| `py-weak-hash` | `hashlib.md5/sha1(...)` | WARNING | AUTO_FIX |
| `py-pickle-untrusted` | `pickle.load/loads($X)` | ERROR | SUGGEST |
| `hardcoded-secrets` | `$VAR = "..."` where VAR matches credential names | ERROR | AUTO_FIX + incident |
| `py-unsafe-yaml-load` | `yaml.load($DATA)` single arg | ERROR | AUTO_FIX |
| `js-eval` | `eval($X)` in JS/TS | ERROR | SUGGEST |
| `risky-templates` | `render_template($T, **$ARGS)` | WARNING | SUGGEST |

Suppression: `# nosemgrep` on a line excludes it from the finding count.
Used only for intentional false positives (e.g. `host='0.0.0.0'` in container, `TESTING=True` in test fixture).

---

## Attack Simulation PRs

| PR | Branch | File added | Rule triggered | Gate fails |
|----|--------|-----------|---------------|-----------|
| #4 | `gate1-sast-test` | `src/test_sql.py` | `py-sql-injection` | Gate 1 SAST |
| #5 | `gate1-secret-test` | `src/test_secret.py` | `hardcoded-secrets` | Gate 1 SAST |
| #6 | `gate2-vuln-dep-test` | `src/test_vuln_dep.py` | `py-unsafe-yaml-load` | Gate 1 SAST |

All three correctly fail `Gate 1 - Code Security Status`. Gate 2 is never reached.

---

## Required Secrets

| Secret | Where used | Effect if missing |
|--------|-----------|------------------|
| `ANTHROPIC_API_KEY` | `pr-security.yml`, `build-security.yml`, `deploy.yml` | Falls back to OpenAI |
| `SNYK_TOKEN` | `security.yml` dependency scan | Scan skipped, job passes |
| `COSIGN_PRIVATE_KEY` | `build-security.yml` | Image signing skipped |
| `SLACK_WEBHOOK_URL` | `auto_remediate.py` incident response | Slack alert skipped |

---

## What Is and Is Not Automated

| Category | Automated? | Where |
|----------|-----------|-------|
| SAST scanning | ✅ Yes | Gate 1, every PR |
| Secret scanning | ✅ Yes | Gate 1, every PR |
| Dependency scanning | ✅ Yes (needs token) | Gate 1, every PR |
| Container CVE scanning | ✅ Yes | Gate 2, after merge |
| SBOM generation | ✅ Yes | Gate 2, after merge |
| AI advisory comment | ✅ Yes | Every PR, non-blocking |
| yaml.load() fix | ✅ Yes — auto-PR | Gate 1 failure |
| Weak hash fix | ✅ Yes — auto-PR | Gate 1 failure |
| Hardcoded secret fix | ✅ Yes — auto-PR + incident | Gate 1 failure |
| subprocess shell=True | 💡 Suggestion only | Gate 1 failure |
| SQL injection fix | ❌ Never | Human required |
| Auth/RBAC fixes | ❌ Never | Human required |
| Container CVE fix | ❌ Never | Human updates Dockerfile |
| Deployment | ❌ Never | Manual trigger + approval |
