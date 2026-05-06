# Testing the AI Security Advisor Workflows

Complete guide to testing the advisor locally and in GitHub Actions.

---

## Prerequisites

```bash
# Install dependencies
pip install -q anthropic  # OR openai
pip install -q pytest

# Verify imports work
python3 -c "from ai_agents import SecurityAdvisor; print('✅ Ready')"
```

---

## Test 1: Local Advisor Testing (No API Calls)

### Run Sample Findings Analysis

```bash
cd /Users/gpreetham/secure-gateway
python3 scripts/run_local_advisor.py
```

**Expected Output:**
```
🔐 Security Advisor Local Testing
======================================================================

TEST 1: Semgrep SAST Findings
======================================================================
Parsed 2 findings from Semgrep
Risk Level: moderate risk
Summary: Found 1 high, 1 medium severity findings.

Generated PR Comment:
🤖 **Security Advisory**
Risk Assessment: moderate risk
...

✅ All advisor tests completed successfully!
```

**What This Tests:**
- ✅ Findings parser works (SARIF JSON)
- ✅ Risk assessment logic
- ✅ PR comment generation
- ✅ Graceful degradation (no LLM API needed)

---

## Test 2: Unit Tests

### Run All Tests

```bash
python3 -m pytest tests/test_advisor.py -v
```

**Expected Output:**
```
tests/test_advisor.py::TestFindingsParser::test_count_by_severity PASSED
tests/test_advisor.py::TestFindingsParser::test_parse_semgrep_findings PASSED
...
tests/test_advisor.py::TestSecurityAdvisorIntegration::test_end_to_end_analysis_and_comment PASSED

============================== 12 passed in 0.02s ==============================
```

**What This Tests:**
- ✅ Findings parser for all scanner formats
- ✅ Risk assessment without LLM
- ✅ Risk assessment with mocked LLM
- ✅ PR comment generation
- ✅ Deployment context generation
- ✅ Graceful degradation on LLM failures
- ✅ Malformed input handling

### Run With Coverage

```bash
python3 -m pytest tests/test_advisor.py --cov=ai_agents --cov-report=html
open htmlcov/index.html
```

---

## Test 3: Local API Testing (With LLM)

### Set API Key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# OR for OpenAI:
export OPENAI_API_KEY="sk-..."
```

### Run Interactive Test

```python
python3 << 'EOF'
from ai_agents import SecurityAdvisor, Finding

advisor = SecurityAdvisor()

# Create a test finding
findings = [
    Finding("semgrep", "HIGH", "SQL Injection", "SELECT * FROM users WHERE id={id}")
]

# Get real LLM analysis
assessment = advisor.analyze_findings(findings)

print(f"Risk Level: {assessment.risk_level}")
print(f"Summary: {assessment.summary}")
print(f"\nPR Comment:\n{advisor.generate_pr_comment(assessment, 'FAIL')}")
EOF
```

**Expected Output:**
```
Risk Level: high risk
Summary: Found 1 high severity findings.

PR Comment:
🤖 **Security Advisory**
Risk Assessment: high risk
Gate Status: FAIL
Summary: Found 1 high severity findings.
...
```

**Cost:** ~$0.01 per request

---

## Test 4: Vulnerable Code Testing

### Create Vulnerable Test PR

1. Create a feature branch:
```bash
git checkout -b test/advisor-vulnerable-code
```

2. Add vulnerable code:
```bash
cp examples/vulnerable_examples.py src/test_vuln.py
```

3. Commit and push:
```bash
git add src/test_vuln.py
git commit -m "test: add vulnerable code for advisor testing"
git push origin test/advisor-vulnerable-code
```

4. Create PR in GitHub (this triggers Gate 1)

5. Watch the workflow:
   - Semgrep detects vulnerabilities
   - Advisor analyzes findings
   - Advisor posts PR comment with guidance

**Expected PR Comment:**
```
🤖 **Security Advisory**

Risk Assessment: high risk
Gate Status: FAIL

Summary: Found 1 critical, 2 high, 3 medium severity findings.

Key Findings:
- [CRITICAL] SQL injection vulnerability
- [HIGH] Hardcoded secret in code
- [HIGH] Weak cryptography (MD5)
- [MEDIUM] Insecure deserialization
- [MEDIUM] Path traversal vulnerability

Recommended Action: fix immediately

This is an advisory assessment. Security gates make the final decision.
```

**What This Tests:**
- ✅ Semgrep integration works
- ✅ Advisor comment posts correctly
- ✅ PR stays blocked (gate decision, not advisor)
- ✅ Developer has clear guidance for fixes

---

## Test 5: Remediation Testing

### Fix the Vulnerable Code

1. Edit `src/test_vuln.py` to use secure patterns:

```python
# Before (vulnerable):
def vulnerable_query(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)

# After (secure):
def secure_query(user_id):
    cursor.execute("SELECT * FROM users WHERE id = ?", [user_id])
```

2. Commit and push:
```bash
git add src/test_vuln.py
git commit -m "fix: use parameterized queries to prevent SQL injection"
git push
```

3. Watch Gate 1 re-run:
   - Semgrep passes (vulnerability fixed)
   - Advisor posts updated comment
   - PR becomes mergeable

**Expected Updated Comment:**
```
🤖 **Security Advisory**

Risk Assessment: low risk
Gate Status: PASS

Summary: No critical or high severity findings.

Recommended Action: proceed

This is an advisory assessment. Security gates make the final decision.
```

**What This Tests:**
- ✅ Advisor updates assessment as vulnerabilities are fixed
- ✅ Gate allows PR after fix
- ✅ Developer sees positive reinforcement

---

## Test 6: Graceful Degradation Testing

### Test Without API Key

1. Update workflow to remove API key:
```yaml
# In .github/workflows/gate-1-code-security.yml
  ai-advisor:
    env:
      ANTHROPIC_API_KEY: ""  # Intentionally empty
```

2. Push a PR with vulnerabilities

3. Verify:
   - ✅ Semgrep still runs and blocks PR
   - ✅ Advisor skips (no API key)
   - ✅ PR is still blocked (gate decides)
   - ✅ No errors in workflow logs

**What This Tests:**
- ✅ Pipeline works without AI layer
- ✅ Gates remain authoritative
- ✅ Graceful degradation works

---

## Test 7: Dependency Vulnerability Testing

### Test Snyk Integration

1. Create branch with vulnerable dependency:
```bash
git checkout -b test/advisor-vulnerable-dependency
```

2. Add old Flask version to requirements.txt:
```bash
echo "flask==1.1.2" >> requirements.txt
```

3. Commit and push:
```bash
git add requirements.txt
git commit -m "test: add vulnerable flask version"
git push origin test/advisor-vulnerable-dependency
```

4. Create PR (triggers Gate 1)

5. Verify:
   - Snyk detects CVE
   - Gate blocks PR
   - Advisor suggests: "Upgrade flask to 2.3.0+"

**Expected Output:**
```
Risk Level: high risk
Recommended Action: fix before deployment

Key Findings:
- [HIGH] flask@1.1.2 - Open redirect vulnerability
  Upgrade to: 2.3.0 or later
```

---

## Test 8: Container Image Testing

### Test Trivy Integration

1. Merge a PR to main (triggers Gate 2)

2. Build Docker image:
```bash
docker build -t secure-gateway:test .
```

3. Run Trivy scan locally:
```bash
trivy image secure-gateway:test --format json > trivy-results.json
```

4. Run advisor on Trivy findings:
```bash
python3 << 'EOF'
from ai_agents import SecurityAdvisor, FindingsParser
import json

with open("trivy-results.json") as f:
    findings = FindingsParser.parse_trivy(f.read())

advisor = SecurityAdvisor()
assessment = advisor.analyze_findings(findings)

context = advisor.generate_deployment_context(findings)
print(context)
EOF
```

**Expected Output:**
```
Deployment Security Context:

🟢 Low Risk - No critical vulnerabilities

Findings: Found X vulnerabilities

Deployment gates enforce policy; this is advisory context.
```

**What This Tests:**
- ✅ Trivy JSON parsing
- ✅ Container vulnerability analysis
- ✅ Deployment context assessment

---

## Test 9: End-to-End CI/CD Testing

### Simulate Full Pipeline

1. Create feature branch:
```bash
git checkout -b test/full-e2e-advisor
```

2. Add code with multiple vulnerability types:
```python
# SQL injection
query = f"SELECT * FROM users WHERE id={user_id}"

# Weak crypto
import hashlib
hash = hashlib.md5(password.encode()).hexdigest()

# Hardcoded secret
API_KEY = "sk_live_1234567890"
```

3. Push and create PR:
```bash
git add .
git commit -m "test: multiple vulnerabilities for e2e testing"
git push origin test/full-e2e-advisor
```

4. Create PR in GitHub

5. Monitor workflow:
   - Gate 1: Run Semgrep, TruffleHog, Snyk
   - Advisor: Analyze all findings
   - Advisor: Post comprehensive PR comment
   - Gate: Blocks PR with combined risk assessment

6. Fix issues one by one:
```bash
# Fix SQL injection
# Fix weak crypto
# Remove secret
git commit -am "fix: remediate security findings"
git push
```

7. Re-run workflow:
   - All gates pass
   - Advisor confirms safe
   - PR mergeable

**What This Tests:**
- ✅ Full Gate 1 workflow
- ✅ Multiple scanner integration
- ✅ Advisor prioritization
- ✅ Iterative remediation flow

---

## Test 10: Cost Monitoring

### Track API Usage

```bash
# For Anthropic:
# Check dashboard: https://console.anthropic.com/

# For OpenAI:
# Check dashboard: https://platform.openai.com/account/billing/overview

# Estimate per-PR cost:
# - Semgrep findings: ~50 tokens
# - Risk assessment: ~200 tokens  
# - Total: ~250 tokens ≈ $0.01 per PR
```

### Log Usage Locally

```python
# Add to analyze_findings.py:
import logging
logging.basicConfig(level=logging.DEBUG)

# Watch for API calls in logs:
# DEBUG:ai_agents.llm_client:Using Anthropic Claude for advisory analysis
```

---

## Troubleshooting

### Tests Fail with Import Errors

```bash
# Ensure you're in the right directory
cd /Users/gpreetham/secure-gateway

# Check PYTHONPATH
export PYTHONPATH=/Users/gpreetham/secure-gateway:$PYTHONPATH

# Run tests again
python3 -m pytest tests/test_advisor.py -v
```

### LLM API Not Responding

```bash
# Check API key
echo $ANTHROPIC_API_KEY

# Test with curl
curl https://api.anthropic.com/v1/health -H "Authorization: Bearer $ANTHROPIC_API_KEY"

# Check rate limits
# Anthropic: 50k tokens/min for free tier
```

### PR Comments Not Posting

```bash
# Check GitHub token permissions in workflow
# Required: pull-requests: write

# Check GitHub Actions logs for errors
# Look for: "Post Advisor Comment" step
```

### Advisor Analysis Not Appearing

```bash
# Check if AI_ADVISOR_INTEGRATION.md steps were followed
# Verify advisor job is in Gate 1 workflow
# Check continue-on-error: true is set
```

---

## Performance Baselines

| Test | Duration | Cost | Notes |
|------|----------|------|-------|
| Unit tests | <1s | $0 | All mocked |
| Local advisor | 5s | $0 | No API calls |
| Real API call | 2-3s | $0.01 | Claude 3.5 |
| Full Gate 1 | 2-3 min | $0.02 | Includes scans |
| Full Gate 2 | 5-10 min | $0.01 | Includes build |
| Full Gate 3 | 2-3 min | $0.01 | If deployed |

---

## Success Criteria

✅ Unit tests: 12/12 passing
✅ Local advisor: All 5 tests passing
✅ Integration: PR comments posting correctly
✅ Degradation: Pipeline works without API key
✅ Cost: <$0.05 per PR
✅ Latency: <5s additional per gate
✅ Documentation: Complete and tested

---

## Next Steps

1. Run all tests locally
2. Set up API key in GitHub Secrets
3. Update Gate 1/2/3 workflows
4. Test with real PRs
5. Monitor costs and performance
6. Iterate based on feedback

