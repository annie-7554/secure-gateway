# AI Advisor Architecture & Role Separation

## Core Principle

**AI Advises. Deterministic Systems Enforce.**

The AI security advisor is a **contextual analysis layer** that works alongside—never replacing—deterministic security gates.

---

## Role Separation

### Deterministic Gates (Authoritative - Enforce)

These systems make final, binding security decisions:

| Gate | Tool | Decision |
|------|------|----------|
| Gate 1 | Semgrep | PASS/FAIL (blocks PR if FAIL) |
| Gate 1 | TruffleHog | PASS/FAIL (blocks PR if FAIL) |
| Gate 1 | Snyk | PASS/FAIL (blocks PR if FAIL) |
| Gate 2 | Trivy | PASS/FAIL (blocks build if FAIL) |
| Gate 2 | SBOM | PASS/FAIL (blocks build if FAIL) |
| Gate 3 | Approval | APPROVED/DENIED (blocks deployment if DENIED) |
| Gate 3 | Kyverno | PASS/FAIL (blocks deployment if FAIL) |
| Gate 3 | RBAC | PASS/FAIL (blocks deployment if FAIL) |

**Responsibility:** These gates are the **source of truth** for security decisions.

**What They Do:**
- ✅ Make binary decisions (PASS/FAIL, ALLOW/DENY)
- ✅ Block PRs, fail builds, deny deployments
- ✅ Enforce policies deterministically
- ✅ Create audit trails for compliance

**What They Don't Do:**
- ❌ Explain context to developers
- ❌ Suggest remediation steps
- ❌ Prioritize findings by business impact
- ❌ Provide deployment readiness assessment

---

### AI Advisory Layer (Contextual - Inform)

This lightweight analysis layer provides developer-facing context:

**Responsibility:** **Inform and guide** developers to understand and fix issues.

**What It Does:**
- ✅ Analyzes gate findings for context
- ✅ Explains risks in developer-friendly language
- ✅ Prioritizes findings by severity
- ✅ Suggests step-by-step remediation
- ✅ Generates PR comments with guidance
- ✅ Assesses deployment safety (advisory)
- ✅ Recommends actions (low risk / moderate risk / high risk)

**What It Doesn't Do:**
- ❌ Block PRs or deployments
- ❌ Override gate decisions
- ❌ Make enforcement decisions
- ❌ Control pipeline flow
- ❌ Become the source of truth

---

## Workflow Integration

### Gate 1: Code Security (Pull Request)

```
┌──────────────────────────────────────────────────┐
│  GitHub Actions: Code Security Job               │
├──────────────────────────────────────────────────┤
│                                                  │
│  [Semgrep, TruffleHog, Snyk run in parallel]    │
│                                                  │
│  Results: Each tool outputs PASS or FAIL        │
│                                                  │
│  ┌─ ENFORCEMENT LOGIC ──────────────────────┐  │
│  │ if any_gate == FAIL:                     │  │
│  │    Block PR (deterministic decision)      │  │
│  │ else if all_gates == PASS:                │  │
│  │    Allow PR (deterministic decision)      │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  [AI Advisor job - Non-Blocking]                │
│  ├─ Receives: Gate findings (SARIF/JSON)       │
│  ├─ Analyzes: Severity, context, priority      │
│  ├─ Generates: Developer-friendly summary      │
│  └─ Posts: PR comment with remediation steps   │
│                                                  │
│  Important: If advisor fails or is unavailable: │
│  └─ PR decision still stands (gates decide)     │
│                                                  │
└──────────────────────────────────────────────────┘
```

**Example Scenario:**

```
1. Developer pushes code with SQL injection
2. Semgrep detects issue → FAIL
3. Gate: PR BLOCKED (enforcement)
4. Advisor: Analyzes finding
5. Advisor: Posts comment with remediation steps
6. Developer: Sees gate block + AI guidance
7. Developer: Fixes issue
8. Semgrep re-scans: PASS
9. Gate: PR ALLOWED (enforcement)
10. Advisor: Confirms safe (advisory)
```

---

### Gate 2: Build Security (Merge to Main)

```
┌──────────────────────────────────────────────────┐
│  GitHub Actions: Build Security Job              │
├──────────────────────────────────────────────────┤
│                                                  │
│  [Build image, run Trivy, generate SBOM]        │
│                                                  │
│  Results: PASS or FAIL for each check           │
│                                                  │
│  ┌─ ENFORCEMENT LOGIC ──────────────────────┐  │
│  │ if any_check == FAIL:                    │  │
│  │    Build FAILED (deterministic)          │  │
│  │ else:                                     │  │
│  │    Build SUCCEEDED (deterministic)        │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  [AI Advisor job - Optional]                    │
│  ├─ Analyzes: Container vulnerabilities        │
│  ├─ Generates: Build summary with upgrade tips │
│  └─ Outputs: Workflow summary                  │
│                                                  │
│  Note: Advisor doesn't affect build decision    │
│                                                  │
└──────────────────────────────────────────────────┘
```

---

### Gate 3: Deployment (Manual Dispatch)

```
┌──────────────────────────────────────────────────┐
│  GitHub Actions: Deployment Gate                 │
├──────────────────────────────────────────────────┤
│                                                  │
│  [Approval check, Kyverno verify, RBAC check]   │
│                                                  │
│  Results: DENIED, FAIL, or PASS                 │
│                                                  │
│  ┌─ ENFORCEMENT LOGIC ──────────────────────┐  │
│  │ if any_check == DENIED or FAIL:          │  │
│  │    Deployment BLOCKED (deterministic)     │  │
│  │ else:                                     │  │
│  │    Deployment PROCEEDS (deterministic)    │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  [AI Advisor job - Informational]               │
│  ├─ Reviews: Deployment context                │
│  ├─ Assesses: Risk level                       │
│  └─ Generates: Deployment summary              │
│                                                  │
│  Note: Advisory for visibility, doesn't change  │
│        deterministic deployment decision        │
│                                                  │
└──────────────────────────────────────────────────┘
```

---

## Graceful Degradation

The pipeline is designed to work perfectly without the advisor:

| Failure Scenario | Deterministic Gates | AI Advisor | Result |
|------------------|-------------------|-----------|--------|
| API key missing | ✅ Work normally | Skipped | Security maintained |
| LLM API down | ✅ Work normally | Failed | Security maintained |
| Parsing error | ✅ Work normally | Fallback | Security maintained |
| GitHub API limited | ✅ Work normally | No comment | Security maintained |
| Advisor crashes | ✅ Work normally | Crashed | Security maintained |

**Principle:** If the advisor is unavailable, the pipeline loses context (developer guidance) but not enforcement (security decisions).

---

## Security Boundaries

### What the Advisor Can See
- Vulnerability reports from scanners (SARIF format)
- Finding severity levels
- Vulnerability descriptions and IDs
- GitHub Actions context (branch, commit, PR number)

### What the Advisor Cannot See
- Source code (unless in finding context)
- Credentials or secrets (sanitized before LLM)
- Private repository information
- GitHub tokens (only for API calls)

### What the Advisor Cannot Do
- Access production systems
- Deploy code or containers
- Modify repositories
- Override gate decisions
- Access databases or external systems
- Persist state (stateless per request)

---

## Prompt Engineering Strategy

### Risk Assessment Prompts

Focus on **business-oriented risk levels**:

```
Instead of: "Severity: HIGH"
Better: "Risk Level: moderate risk - requires fix before deployment"

Instead of: "CVSS Score: 7.5"
Better: "Risk Level: high risk - critical business impact if exploited"
```

### Remediation Prompts

Focus on **practical developer steps**:

```
Instead of: "Use parameterized queries"
Better: "Replace 'query = f\"SELECT * FROM users WHERE id={user_id}\"' 
         with 'cursor.execute('SELECT * FROM users WHERE id=?', [user_id])'"
```

### Assessment Prompts

Focus on **actionable guidance**:

```
Instead of: "This is a security issue"
Better: "This vulnerability allows SQL injection attacks. Fix by using 
         parameterized queries. Estimated time: 15 minutes."
```

---

## Why This Architecture Works

### For Security Teams
- ✅ Deterministic gates enforce policies
- ✅ Audit trail remains clean (gates make decisions)
- ✅ No AI-based enforcement (stays compliant)
- ✅ Graceful degradation (AI failure ≠ security failure)

### For Developers
- ✅ Clear explanation of why something blocked
- ✅ Step-by-step remediation guidance
- ✅ Faster time-to-fix (AI-assisted learning)
- ✅ Contextual understanding of risks

### For Maintainers
- ✅ Lightweight, stateless implementation
- ✅ No complex orchestration frameworks
- ✅ Easy to debug (each component independent)
- ✅ Easy to disable (no hard dependencies)

### For Organizations
- ✅ Security remains deterministic and auditable
- ✅ Cost-effective (advisory is optional)
- ✅ Scalable (advisory doesn't block critical path)
- ✅ Future-proof (easy to swap LLM providers)

---

## Interview Explanation

> "We have a three-stage security pipeline where deterministic gates make binary enforce/deny decisions. On top of that, we added an AI advisory layer that provides contextual analysis.
>
> The gates handle enforcement—they block PRs, fail builds, deny deployments. The AI handles guidance—it explains findings to developers in plain language and suggests how to fix them.
>
> The critical design principle is that if the AI service completely fails, the pipeline still works. Gates are independent. The AI enhances developer experience but never becomes responsible for enforcement.
>
> This keeps security rigorous while improving how developers understand and respond to vulnerabilities."

---

## Production Deployment Checklist

- [ ] API keys configured (ANTHROPIC_API_KEY in GitHub Secrets)
- [ ] GitHub Actions permissions set (pull-requests: write, security-events: write)
- [ ] Advisor scripts installed in `scripts/` directory
- [ ] Tests passing (12/12 in test_advisor.py)
- [ ] Local testing works: `python3 scripts/run_local_advisor.py`
- [ ] Gate 1 workflow updated with advisor job
- [ ] Gate 2 workflow updated with advisor job
- [ ] Gate 3 workflow updated with advisor job
- [ ] PR comments tested with real findings
- [ ] Documentation reviewed and updated
- [ ] Cost monitoring set up (API usage tracking)
- [ ] Fallback behavior tested (disable API key, verify gates still work)

---

## Further Reading

- `ADVISORY_ARCHITECTURE.md` - Detailed architecture diagrams
- `AI_ADVISOR_INTEGRATION.md` - Integration step-by-step guide
- `TESTING_WORKFLOW.md` - Full testing walkthroughs
