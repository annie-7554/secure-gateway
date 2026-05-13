# Quick Reference

## Gate Status at a Glance

| Gate | Workflow | Trigger | Must pass before |
|------|----------|---------|-----------------|
| Gate 1 — Code Security | `security.yml` | PR + push to main | Gate 2 can run |
| Gate 2 — Container Security | `build.yml` + `build-security.yml` | Gate 1 success (workflow_run) | Gate 3 |
| Gate 3 — Secure Deploy | `deploy.yml` | Manual + human approval | Production |
| AI Advisory | `pr-security.yml` | Every PR | Non-blocking |
| Auto-Remediation | `auto-remediate.yml` | Gate 1 failure on PR | n/a |

## Semgrep Custom Rules

| Rule | What it catches |
|------|----------------|
| `py-sql-injection` | `cursor.execute(query)` without params |
| `py-eval-exec` | `eval()` / `exec()` |
| `py-subprocess-shell` | `subprocess.run(shell=True)` |
| `py-weak-hash` | `hashlib.md5` / `hashlib.sha1` |
| `py-pickle-untrusted` | `pickle.load` / `pickle.loads` |
| `hardcoded-secrets` | Variable names matching credential patterns assigned string literals |
| `py-unsafe-yaml-load` | `yaml.load()` without safe Loader |
| `js-eval` | `eval()` in JavaScript |
| `risky-templates` | `render_template($T, **$ARGS)` |

## Auto-Remediation Tiers

| Tier | Rules | What happens |
|------|-------|-------------|
| AUTO_FIX | `py-unsafe-yaml-load`, `py-weak-hash`, `hardcoded-secrets` | Code fixed → validated → draft PR opened |
| SUGGEST | `py-subprocess-shell`, `py-eval-exec`, `py-pickle-untrusted`, `js-eval`, `risky-templates` | Suggestion posted, no code change |
| ESCALATE | `py-sql-injection`, CRITICAL severity, auth/RBAC/infra categories, unknown rules | Human guidance posted, merge blocked |

## Secrets Required

| Secret | Used by |
|--------|---------|
| `ANTHROPIC_API_KEY` | AI advisory comments |
| `SNYK_TOKEN` | Dependency CVE scanning |
| `COSIGN_PRIVATE_KEY` | Container image signing |
| `SLACK_WEBHOOK_URL` | Secret exposure incident alerts |

## Attack Simulation PRs

| PR | Branch | Fails at |
|----|--------|---------|
| #4 | `gate1-sast-test` | Gate 1 SAST — `py-sql-injection` |
| #5 | `gate1-secret-test` | Gate 1 SAST — `hardcoded-secrets` |
| #6 | `gate2-vuln-dep-test` | Gate 1 SAST — `py-unsafe-yaml-load` |

## Run Locally

```bash
# Tests
pytest -q

# Semgrep custom rules only
semgrep --config .semgrep/rules.yml .

# Semgrep full scan (matches CI)
semgrep --config .semgrep/rules.yml \
        --config p/security-audit \
        --config p/owasp-top-ten \
        --config p/cwe-top-25 .

# Auto-remediation dry run
python3 scripts/auto_remediate.py --sarif semgrep.sarif --dry-run

# AI advisor
python3 scripts/analyze_findings.py --semgrep-sarif semgrep.sarif --gate gate1
```
