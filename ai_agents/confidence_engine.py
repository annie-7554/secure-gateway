"""Confidence engine — classifies findings by remediation confidence level.

HIGH   → deterministic 1:1 fix, safe to auto-PR
MEDIUM → fix is known but context-sensitive, suggest only
LOW    → fix requires understanding app logic, human escalation
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Confidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class RemediationProfile:
    confidence: Confidence
    auto_fix: Optional[str]   # brief description of the automated fix
    suggestion: str            # what to tell developer
    requires_incident: bool = False  # triggers incident response (secrets)


# Rule ID → remediation profile
# Only HIGH confidence rules get auto-PRs. Everything else is suggest or escalate.
RULE_PROFILES: dict[str, RemediationProfile] = {
    # ── HIGH confidence: deterministic 1:1 replacements ─────────────────────
    "py-unsafe-yaml-load": RemediationProfile(
        confidence=Confidence.HIGH,
        auto_fix="Replace yaml.load($DATA) with yaml.safe_load($DATA)",
        suggestion="Use `yaml.safe_load()` — it only deserializes basic types and cannot execute arbitrary code.",
    ),
    "py-weak-hash": RemediationProfile(
        confidence=Confidence.HIGH,
        auto_fix="Replace hashlib.md5/sha1 with hashlib.sha256",
        suggestion="Use `hashlib.sha256()` or stronger. MD5/SHA1 are broken for security purposes.",
    ),
    "hardcoded-secrets": RemediationProfile(
        confidence=Confidence.HIGH,
        auto_fix="Replace string literal with os.getenv('<VAR_NAME>')",
        suggestion="Store secrets in environment variables. Never commit credentials to source control.",
        requires_incident=True,
    ),

    # ── MEDIUM confidence: fix is known but context-sensitive ────────────────
    "py-subprocess-shell": RemediationProfile(
        confidence=Confidence.MEDIUM,
        auto_fix=None,
        suggestion=(
            "Replace `shell=True` with a list of arguments: "
            "`subprocess.run(['cmd', 'arg1', 'arg2'])`. "
            "Review the command to ensure list form is safe."
        ),
    ),
    "py-eval-exec": RemediationProfile(
        confidence=Confidence.MEDIUM,
        auto_fix=None,
        suggestion=(
            "Remove `eval`/`exec`. Consider `ast.literal_eval()` for safe "
            "expression parsing, or refactor to eliminate dynamic execution."
        ),
    ),
    "py-pickle-untrusted": RemediationProfile(
        confidence=Confidence.MEDIUM,
        auto_fix=None,
        suggestion=(
            "Replace `pickle` with `json` or `msgpack` for untrusted data. "
            "If pickle is required, validate the source is trusted before deserializing."
        ),
    ),
    "js-eval": RemediationProfile(
        confidence=Confidence.MEDIUM,
        auto_fix=None,
        suggestion="Remove `eval()`. Use `JSON.parse()` for data or refactor logic.",
    ),

    # ── LOW confidence: fix requires app-level understanding ─────────────────
    "py-sql-injection": RemediationProfile(
        confidence=Confidence.LOW,
        auto_fix=None,
        suggestion=(
            "Use parameterized queries: `cursor.execute(query, (param,))`. "
            "The fix requires understanding the data model — human review required."
        ),
    ),
    "risky-templates": RemediationProfile(
        confidence=Confidence.LOW,
        auto_fix=None,
        suggestion=(
            "Sanitize user input before passing to templates. "
            "Review all `**kwargs` expansion into render_template calls."
        ),
    ),
}

# Severity → confidence floor (CRITICAL findings always go to human)
SEVERITY_FLOOR: dict[str, Confidence] = {
    "CRITICAL": Confidence.LOW,
    "HIGH": Confidence.MEDIUM,
    "MEDIUM": Confidence.HIGH,
    "LOW": Confidence.HIGH,
    "INFO": Confidence.HIGH,
}


def classify(rule_id: str, severity: str) -> RemediationProfile:
    """Return the remediation profile for a finding.

    Severity can demote confidence: a CRITICAL finding is never auto-fixed
    even if we have a known pattern for it.
    """
    profile = RULE_PROFILES.get(rule_id)

    if profile is None:
        return RemediationProfile(
            confidence=Confidence.LOW,
            auto_fix=None,
            suggestion="Unknown rule — review manually and consult the scanner documentation.",
        )

    floor = SEVERITY_FLOOR.get(severity.upper(), Confidence.LOW)
    # Demote if severity demands it
    order = [Confidence.HIGH, Confidence.MEDIUM, Confidence.LOW]
    effective = order[max(order.index(profile.confidence), order.index(floor))]

    if effective == profile.confidence:
        return profile

    return RemediationProfile(
        confidence=effective,
        auto_fix=None,  # demoted — no auto-fix
        suggestion=profile.suggestion,
        requires_incident=profile.requires_incident,
    )
