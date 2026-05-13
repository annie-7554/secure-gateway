"""Remediation policy engine.

Core principle
--------------
AI remediation is intentionally restricted to a narrow set of deterministic,
low-risk, reversible fixes. Everything else is escalated to human review.

The boundary is defined by two questions:
  1. Is the fix pattern unambiguous regardless of app context?
  2. If the fix is wrong, can a PR review catch it before it reaches main?

If both answers are YES → AUTO_FIX
If the fix touches business logic, auth, or infrastructure → HUMAN_REQUIRED

This restriction is intentional. Allowing AI to modify auth logic, SQL queries,
or RBAC rules risks hallucinated fixes, broken business logic, and production
incidents that are difficult to trace back to the automation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Action(str, Enum):
    AUTO_FIX = "AUTO_FIX"        # apply fix, validate, open draft PR
    SUGGEST   = "SUGGEST"         # post inline suggestion, no code change
    ESCALATE  = "ESCALATE"        # human required — post detailed guidance


@dataclass
class RemediationPolicy:
    action: Action
    rationale: str           # why this action tier was chosen
    fix_description: Optional[str] = None   # only set for AUTO_FIX
    guidance: str = ""       # developer-facing suggestion or escalation text
    requires_incident: bool = False


# ── SAFE FOR AI AUTO-REMEDIATION ────────────────────────────────────────────
# Criteria: deterministic pattern, low blast radius, easily tested, reversible.
# The fix is the same regardless of what the surrounding business logic does.

AUTO_FIX_RULES: dict[str, RemediationPolicy] = {

    "py-unsafe-yaml-load": RemediationPolicy(
        action=Action.AUTO_FIX,
        rationale="1:1 function substitution — yaml.safe_load is a drop-in replacement with no behavior change for valid input.",
        fix_description="Replace yaml.load($DATA) → yaml.safe_load($DATA)",
        guidance="yaml.safe_load() deserializes only basic Python types. It cannot execute arbitrary code.",
    ),

    "py-weak-hash": RemediationPolicy(
        action=Action.AUTO_FIX,
        rationale="Industry-known replacement pattern. SHA-256 is a drop-in for MD5/SHA-1 in non-password contexts.",
        fix_description="Replace hashlib.md5/sha1 → hashlib.sha256",
        guidance="Use hashlib.sha256() or stronger. For passwords, use bcrypt or argon2 instead.",
    ),

    "hardcoded-secrets": RemediationPolicy(
        action=Action.AUTO_FIX,
        rationale="Standardized remediation: string literal → os.getenv(). Pattern is unambiguous.",
        fix_description="Replace string literal → os.getenv('<VAR_NAME>')",
        guidance="Store secrets in environment variables. Rotate the exposed credential immediately.",
        requires_incident=True,   # also triggers incident response
    ),
}


# ── SUGGEST ONLY — pattern known but context matters ────────────────────────
# AI posts a precise suggestion. Developer applies it after reviewing context.
# These are excluded from AUTO_FIX because applying the fix incorrectly could
# break functionality or introduce a different vulnerability.

SUGGEST_RULES: dict[str, RemediationPolicy] = {

    "py-subprocess-shell": RemediationPolicy(
        action=Action.SUGGEST,
        rationale="Fix is known but requires understanding the command being run. Wrong list-form args can silently change behavior.",
        guidance=(
            "Replace shell=True with a list of arguments:\n"
            "  subprocess.run(['cmd', 'arg1', 'arg2'])\n"
            "Review each argument carefully — shell globbing and quoting "
            "behave differently in list form."
        ),
    ),

    "py-eval-exec": RemediationPolicy(
        action=Action.SUGGEST,
        rationale="eval/exec removal requires understanding intent. ast.literal_eval is not always a valid replacement.",
        guidance=(
            "Remove eval()/exec(). Options:\n"
            "  - ast.literal_eval() for safe expression parsing\n"
            "  - json.loads() for data deserialization\n"
            "  - Refactor to eliminate dynamic execution entirely"
        ),
    ),

    "py-pickle-untrusted": RemediationPolicy(
        action=Action.SUGGEST,
        rationale="Replacement depends on the serialization format in use. json/msgpack are not always compatible.",
        guidance=(
            "Replace pickle with json or msgpack for untrusted input. "
            "If pickle is required, ensure the data source is fully trusted "
            "and isolated from user input."
        ),
    ),

    "js-eval": RemediationPolicy(
        action=Action.SUGGEST,
        rationale="eval() removal depends on what the code is evaluating.",
        guidance="Remove eval(). Use JSON.parse() for data or refactor the logic to avoid dynamic execution.",
    ),

    "risky-templates": RemediationPolicy(
        action=Action.SUGGEST,
        rationale="Template rendering with **kwargs is context-specific. Sanitization strategy depends on data shape.",
        guidance=(
            "Sanitize user-controlled values before passing to render_template. "
            "Consider explicit variable passing instead of **kwargs expansion."
        ),
    ),
}


# ── HUMAN REQUIRED — never auto-remediate ───────────────────────────────────
# These categories are excluded because:
#   - The fix depends on business logic AI cannot understand
#   - A wrong fix could introduce a worse vulnerability
#   - The blast radius extends beyond the changed line
#
# This is an intentional policy constraint, not a technical limitation.

HUMAN_REQUIRED_RULES: dict[str, RemediationPolicy] = {

    "py-sql-injection": RemediationPolicy(
        action=Action.ESCALATE,
        rationale=(
            "SQL injection fixes require understanding the query's role in business logic. "
            "AI may break joins, transactions, filters, or ORM behavior. "
            "Parameterization strategy must be reviewed by a developer."
        ),
        guidance=(
            "Use parameterized queries: cursor.execute(query, (param,))\n"
            "Do NOT use string formatting or concatenation in SQL.\n"
            "Review the full query context — joins, transactions, and ORM "
            "interactions must be verified after the fix."
        ),
    ),
}

# Categories that are always HUMAN_REQUIRED regardless of rule ID
# Used to classify findings from external scanners (Trivy, Snyk, TruffleHog)
HUMAN_REQUIRED_CATEGORIES = {
    "authentication",    # JWT, OAuth, MFA, session handling
    "authorization",     # RBAC, permissions, tenant isolation
    "business-logic",    # race conditions, workflow bypass, payment flows
    "infrastructure",    # IAM, firewall, Kubernetes RBAC, VPC
    "major-upgrade",     # semver major version bumps
    "zero-day",          # no trusted remediation pattern yet
    "data-migration",    # schema changes, encryption migration
}


# ── Severity override ────────────────────────────────────────────────────────
# CRITICAL severity always escalates to human regardless of rule confidence.
# The blast radius of a wrong CRITICAL fix outweighs the benefit of automation.
CRITICAL_ALWAYS_ESCALATES = True


def get_policy(rule_id: str, severity: str, category: str = "") -> RemediationPolicy:
    """Return the remediation policy for a finding.

    Lookup order:
      1. CRITICAL severity → always ESCALATE
      2. Category in HUMAN_REQUIRED_CATEGORIES → always ESCALATE
      3. Rule in AUTO_FIX_RULES → AUTO_FIX
      4. Rule in SUGGEST_RULES → SUGGEST
      5. Rule in HUMAN_REQUIRED_RULES → ESCALATE
      6. Unknown rule → ESCALATE (fail safe)
    """
    sev = severity.upper()
    # Map scanner severity words to standard levels
    sev = {"ERROR": "HIGH", "WARNING": "MEDIUM", "NOTE": "LOW"}.get(sev, sev)

    if CRITICAL_ALWAYS_ESCALATES and sev == "CRITICAL":
        return RemediationPolicy(
            action=Action.ESCALATE,
            rationale="CRITICAL severity always requires human review — automated fixes are disabled at this severity level.",
            guidance="This finding is severity CRITICAL. Manual review and approval required before any remediation.",
        )

    if category.lower() in HUMAN_REQUIRED_CATEGORIES:
        return RemediationPolicy(
            action=Action.ESCALATE,
            rationale=f"Category '{category}' is excluded from AI auto-remediation by policy.",
            guidance=f"Findings in the '{category}' category require human review. AI remediation is intentionally disabled here.",
        )

    for lookup in (AUTO_FIX_RULES, SUGGEST_RULES, HUMAN_REQUIRED_RULES):
        if rule_id in lookup:
            return lookup[rule_id]

    # Unknown rule — fail safe: escalate
    return RemediationPolicy(
        action=Action.ESCALATE,
        rationale="Unknown rule — no remediation policy registered. Defaulting to human escalation (fail-safe).",
        guidance="Review the scanner output and consult the security team for remediation guidance.",
    )


# ── Policy summary (for PR comments and documentation) ───────────────────────

POLICY_STATEMENT = """
**AI Remediation Policy**

The pipeline restricts automated remediation to a narrow set of
deterministic, low-risk, reversible fixes. Context-sensitive or
security-critical findings are always escalated to human review.

| Category | AI Auto-Fix? |
|----------|-------------|
| Hardcoded secrets | ✅ Yes — replace with `os.getenv()` |
| Weak hashing (MD5/SHA-1) | ✅ Yes — replace with SHA-256 |
| Unsafe yaml.load() | ✅ Yes — replace with yaml.safe_load() |
| subprocess shell=True | 💡 Suggest only |
| eval() / exec() | 💡 Suggest only |
| SQL injection | ❌ No — business logic context required |
| Authentication logic | ❌ No — security-critical, never automated |
| Authorization / RBAC | ❌ No — privilege escalation risk |
| Infrastructure (IAM, firewall) | ❌ No — outage/exposure risk |
| Major dependency upgrades | ❌ No — API breaking changes possible |
| Business logic flaws | ❌ No — app context required |
| Zero-day vulnerabilities | ❌ No — no trusted pattern yet |

All auto-fix PRs are draft and require developer approval before merging.
""".strip()
