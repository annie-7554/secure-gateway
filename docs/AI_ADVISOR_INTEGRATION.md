# AI Security Advisor Integration Guide

## Overview

The AI Security Advisor provides lightweight, advisory-only security analysis alongside deterministic security gates. This guide shows how to integrate it into your GitHub Actions workflows.

**Key Principle:** AI advises, deterministic gates enforce.

---

## Architecture

```
GitHub Actions Workflow
    ↓
[Deterministic Gate: Semgrep/TruffleHog/Snyk]
    ↓ (PASS or FAIL)
[AI Advisor: Parse findings → Analyze → Generate context]
    ↓
[Post PR comment / Workflow summary]
    ↓
Deterministic gate decision stands (AI doesn't change it)
```

---

## Integration Steps

### 1. Add Advisor Dependencies

Update `requirements.txt`:

```txt
# Existing dependencies
flask==2.3.3
semgrep==1.45.0
...

# Add for AI advisor
anthropic==0.28.0  # OR openai==1.5.0 for OpenAI
```

### 2. Add Secrets

In GitHub repository settings → Secrets and variables → Actions:

```
ANTHROPIC_API_KEY     # OR OPENAI_API_KEY for OpenAI
```

(Optional - advisor gracefully degrades without API key)

### 3. Update Gate 1 Workflow (Code Security)

Modify `.github/workflows/gate-1-code-security.yml`:

```yaml
name: Gate 1 - Code Security

on:
  pull_request:
    branches: [main]

permissions:
  contents: read
  security-events: write
  pull-requests: write  # For posting comments

jobs:
  semgrep:
    runs-on: ubuntu-latest
    outputs:
      semgrep-results: ${{ steps.semgrep.outputs.results }}
    steps:
      - uses: actions/checkout@v4
      
      - name: Semgrep SAST Scan
        id: semgrep
        run: |
          semgrep --config p/security-audit --json --output results.json .
          echo "results=$(cat results.json)" >> $GITHUB_OUTPUT
        continue-on-error: true
      
      - name: Check Semgrep Results
        if: failure()
        run: exit 1

  # ... TruffleHog and Snyk jobs ...

  ai-advisor:
    runs-on: ubuntu-latest
    needs: [semgrep, trufflehog, snyk]
    if: always()  # Run even if previous jobs fail
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Advisor
        run: |
          pip install -q anthropic  # or openai
          pip install -q -e .
      
      - name: Run AI Advisor
        id: advisor
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python3 scripts/analyze_findings.py \
            --findings-json "${{ needs.semgrep.outputs.semgrep-results }}" \
            --gate-status "GATE1" \
            --pr-number "${{ github.event.number }}"
        continue-on-error: true  # Don't fail workflow
      
      - name: Post Advisor Comment
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const comment = `${{ steps.advisor.outputs.pr-comment }}`;
            if (comment) {
              github.rest.issues.createComment({
                issue_number: context.issue.number,
                owner: context.repo.owner,
                repo: context.repo.repo,
                body: comment
              });
            }
        continue-on-error: true
```

### 4. Update Gate 2 Workflow (Build Security)

Add advisor job to `.github/workflows/gate-2-build-security.yml`:

```yaml
  ai-advisor:
    runs-on: ubuntu-latest
    needs: [trivy-scan, sbom-generation]
    if: always()
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Advisor
        run: |
          pip install -q anthropic
          pip install -q -e .
      
      - name: Analyze Build Findings
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python3 scripts/analyze_findings.py \
            --findings-file trivy-results.json \
            --gate-status "GATE2" \
            --workflow-summary
        continue-on-error: true
      
      - name: Upload Advisor Report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: advisor-report
          path: advisor-summary.json
```

### 5. Update Gate 3 Workflow (Deployment)

Add advisor for deployment context in `.github/workflows/gate-3-deployment.yml`:

```yaml
  ai-advisor-deployment:
    runs-on: ubuntu-latest
    needs: [approval-check, kyverno-verify, rbac-check]
    if: always()
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Advisor
        run: |
          pip install -q anthropic
          pip install -q -e .
      
      - name: Generate Deployment Context
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python3 scripts/analyze_findings.py \
            --gate-status "GATE3" \
            --deployment-context
        continue-on-error: true
```

---

## Analysis Scripts

### Gate 1/2/3 Analysis Script

Create `scripts/analyze_findings.py`:

```python
#!/usr/bin/env python3
"""Analyze security findings and generate advisor context."""

import json
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_agents import SecurityAdvisor, FindingsParser

def main():
    parser = argparse.ArgumentParser(description="Analyze security findings")
    parser.add_argument("--findings-json", help="JSON findings string")
    parser.add_argument("--findings-file", help="JSON findings file")
    parser.add_argument("--gate-status", required=True, help="GATE1|GATE2|GATE3")
    parser.add_argument("--pr-number", type=int, help="PR number for comment")
    parser.add_argument("--workflow-summary", action="store_true")
    parser.add_argument("--deployment-context", action="store_true")
    
    args = parser.parse_args()
    
    # Parse findings
    findings = []
    
    if args.findings_json:
        # Parse from command line JSON
        try:
            data = json.loads(args.findings_json)
            findings = FindingsParser.parse_semgrep(json.dumps(data))
        except json.JSONDecodeError:
            print("Warning: Could not parse findings JSON")
    
    elif args.findings_file:
        # Parse from file
        try:
            with open(args.findings_file) as f:
                findings = FindingsParser.parse_trivy(f.read())
        except FileNotFoundError:
            print(f"Warning: Findings file not found: {args.findings_file}")
    
    # Create advisor
    advisor = SecurityAdvisor()
    
    # Analyze
    assessment = advisor.analyze_findings(findings)
    
    # Generate output based on mode
    if args.deployment_context:
        context = advisor.generate_deployment_context(findings)
        print(context)
    elif args.workflow_summary:
        summary = {
            "risk_level": assessment.risk_level,
            "summary": assessment.summary,
            "recommended_action": assessment.recommended_action
        }
        print(json.dumps(summary, indent=2))
        with open("advisor-summary.json", "w") as f:
            json.dump(summary, f, indent=2)
    else:
        # PR comment mode
        comment = advisor.generate_pr_comment(assessment, args.gate_status)
        print("::set-output name=pr-comment::" + comment.replace("\n", "%0A"))
        print(comment)

if __name__ == "__main__":
    main()
```

---

## Features by Gate

### Gate 1: Code Security
- ✅ Parse Semgrep SAST findings
- ✅ Parse TruffleHog secret findings
- ✅ Parse Snyk dependency findings
- ✅ Risk assessment: low risk / moderate risk / high risk
- ✅ PR comment with remediation guidance
- ✅ Graceful degradation if LLM unavailable

**Example Output:**
```
🤖 Security Advisory

Risk Assessment: moderate risk
Gate Status: FAIL

Summary: Found 1 high, 2 medium severity findings.

Key Findings:
- [HIGH] SQL injection vulnerability
- [MEDIUM] Weak cryptography detected

Recommended Action: fix before deployment

This is an advisory assessment. Security gates make the final decision.
```

### Gate 2: Build Security
- ✅ Parse Trivy container findings
- ✅ Parse SBOM data
- ✅ Risk prioritization
- ✅ Workflow summary with severity breakdown
- ✅ Deployment readiness assessment

### Gate 3: Deployment
- ✅ Deployment security context
- ✅ Risk assessment (low/moderate/high)
- ✅ Critical blocker identification
- ✅ Production monitoring caveats

---

## Local Testing

Run the local advisor test:

```bash
cd /Users/gpreetham/secure-gateway
python3 scripts/run_local_advisor.py
```

Expected output shows risk assessments for Semgrep, Snyk, and Trivy findings.

---

## Running Tests

```bash
python3 -m pytest tests/test_advisor.py -v
```

All tests use mocked LLM responses (no real API calls required).

---

## Environment Variables

```bash
# Option 1: Anthropic Claude (Recommended)
export ANTHROPIC_API_KEY="sk-ant-..."

# Option 2: OpenAI GPT
export OPENAI_API_KEY="sk-..."

# Or configure in GitHub Secrets
```

---

## Graceful Degradation

The advisor gracefully handles failures:

| Scenario | Result |
|----------|--------|
| API key missing | Advisor skipped, gates still work |
| LLM API down | Fallback assessment, gates still work |
| Parsing error | Basic summary, gates still work |
| GitHub API limited | No comment posted, gates still work |

**Security enforcement is never affected by advisor availability.**

---

## Cost Optimization

- Claude API: ~$0.03 per request (usually < 100 tokens)
- OpenAI API: ~$0.0005 per request (mini model)
- Per PR: ~$0.01-0.05 depending on provider and findings size
- Advisor is optional - can be disabled by not setting API key

---

## Troubleshooting

### Advisor not posting comments
- Check GitHub token permissions (needs `pull-requests: write`)
- Verify `ANTHROPIC_API_KEY` is set in Secrets
- Check workflow logs for errors in `analyze_findings.py`

### API rate limits
- Add exponential backoff in analyze_findings.py
- Use queue-based batching for high-volume repos
- Monitor API quota in Anthropic/OpenAI dashboard

### JSON parsing errors
- Verify findings format matches scanner output
- Check for special characters in findings
- Use JSON validation before passing to advisor

---

## Next Steps

1. ✅ Core advisor modules implemented
2. ✅ Tests passing (12/12)
3. ✅ Local advisor script working
4. → Update Gate 1/2/3 workflows with advisor integration
5. → Test end-to-end with actual PRs
6. → Monitor advisor performance and costs

---

## More Information

See `/docs/` for:
- `ADVISORY_ARCHITECTURE.md` - Design and principles
- `PROMPTS_AND_CONTEXT.md` - Prompt engineering details
- `TESTING_WORKFLOW.md` - Step-by-step testing guide
