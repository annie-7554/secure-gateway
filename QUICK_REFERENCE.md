# Quick Reference: AI Security Advisor

## 🚀 Start Here

### Verify Installation
```bash
cd /Users/gpreetham/secure-gateway

# Test imports
python3 -c "from ai_agents import SecurityAdvisor; print('✅ Ready')"

# Run local tests (5 scenarios)
python3 scripts/run_local_advisor.py

# Run unit tests (12 tests)
python3 -m pytest tests/test_advisor.py -v
```

### Expected Output
```
✅ All advisor tests completed successfully!
============================== 12 passed in 0.02s ==============================
```

---

## 📖 Documentation Map

| Document | Content | Read When |
|----------|---------|-----------|
| **ADVISORY_ARCHITECTURE.md** | Design, role separation, principles | Understanding the design |
| **AI_ADVISOR_INTEGRATION.md** | Step-by-step GitHub Actions integration | Integrating with workflows |
| **TESTING_WORKFLOW.md** | 10 complete testing scenarios | Testing the advisor |
| **AI_ADVISOR_IMPLEMENTATION_SUMMARY.md** | Project overview & status | Getting the big picture |

---

## 🔧 Integration Checklist

```
□ Install dependencies: pip install anthropic
□ Configure GitHub Secrets: ANTHROPIC_API_KEY
□ Update Gate 1 workflow (code security)
□ Update Gate 2 workflow (build security)
□ Update Gate 3 workflow (deployment)
□ Test with real PR (vulnerable code)
□ Monitor costs and performance
□ Gather developer feedback
```

---

## 💡 Key Files

**Core Modules:**
- `ai_agents/security_advisor.py` - Main orchestration
- `ai_agents/llm_client.py` - LLM API abstraction
- `ai_agents/findings_parser.py` - Scanner parsing
- `ai_agents/advisor_prompts.py` - Prompt templates

**Testing:**
- `tests/test_advisor.py` - 12 unit tests (all passing)
- `scripts/run_local_advisor.py` - Local testing (5 scenarios)

**Documentation:**
- `docs/ADVISORY_ARCHITECTURE.md` - Design guide
- `docs/AI_ADVISOR_INTEGRATION.md` - Integration guide
- `docs/TESTING_WORKFLOW.md` - Testing guide

---

## 🧪 Quick Testing

### Test 1: Unit Tests
```bash
python3 -m pytest tests/test_advisor.py -v
```
Expected: 12 PASSED in <1s

### Test 2: Local Advisor (5 Scenarios)
```bash
python3 scripts/run_local_advisor.py
```
Expected: All scenarios pass (Semgrep, Snyk, Trivy, degradation, counting)

### Test 3: With Real API Key
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python3 << 'EOF'
from ai_agents import SecurityAdvisor, Finding

advisor = SecurityAdvisor()
findings = [Finding("semgrep", "HIGH", "SQL Injection", "Unsafe query")]
assessment = advisor.analyze_findings(findings)
print(f"Risk: {assessment.risk_level}")
print(advisor.generate_pr_comment(assessment, "FAIL"))
EOF
```

---

## 📊 Architecture at a Glance

```
┌─ Gate 1: Code Security ──────────────────┐
│ Semgrep/TruffleHog/Snyk: PASS or FAIL     │
│ └─ AI Advisor: Analyze findings → Comment │
└──────────────────────────────────────────┘

┌─ Gate 2: Build Security ─────────────────┐
│ Trivy/SBOM: PASS or FAIL                  │
│ └─ AI Advisor: Analyze findings → Summary │
└──────────────────────────────────────────┘

┌─ Gate 3: Deployment ─────────────────────┐
│ Approval/Kyverno/RBAC: PASS or FAIL       │
│ └─ AI Advisor: Context assessment         │
└──────────────────────────────────────────┘
```

**Key Principle:** Gates enforce. Advisor informs.

---

## 🔐 Role Separation

| Aspect | Gates | Advisor |
|--------|-------|---------|
| **Decides** | PASS/FAIL | Low/Moderate/High Risk |
| **Blocks** | ✅ Yes | ❌ No |
| **Comments** | ❌ No | ✅ Yes |
| **Authority** | ✅ Yes | ❌ No |
| **Enforces** | ✅ Yes | ❌ No |
| **Guides** | ❌ No | ✅ Yes |

---

## 💰 Cost Estimate

| Scenario | Cost | Notes |
|----------|------|-------|
| Per PR with AI | $0.01 | Anthropic Claude |
| Per PR with AI | $0.0005 | OpenAI mini |
| Without AI | $0 | If key not set |
| 100 PRs/month | $1 | Manageable cost |

---

## ⚠️ Common Pitfalls to Avoid

❌ **Don't:** Make advisor decision-making
✅ **Do:** Let gates decide, advisor advises

❌ **Don't:** Require API key (make it optional)
✅ **Do:** Graceful degradation when API unavailable

❌ **Don't:** Add complex orchestration
✅ **Do:** Keep it lightweight and simple

❌ **Don't:** Expose sensitive data to LLM
✅ **Do:** Sanitize findings before sending

❌ **Don't:** Make advisor blocking
✅ **Do:** Run as non-blocking optional job

---

## 🆘 Troubleshooting

### Tests Failing with Import Error
```bash
cd /Users/gpreetham/secure-gateway
python3 -m pytest tests/test_advisor.py -v
```

### API Key Not Working
```bash
# Check key is set
echo $ANTHROPIC_API_KEY

# Test API directly
curl https://api.anthropic.com/ \
  -H "Authorization: Bearer $ANTHROPIC_API_KEY"
```

### PR Comments Not Posting
```bash
# Check workflow permissions in GitHub:
# Required: pull-requests: write, security-events: write

# Check GitHub Actions logs for errors
```

---

## 📚 Learning Path

1. **Understand the architecture** → Read ADVISORY_ARCHITECTURE.md
2. **See it working locally** → Run `python3 scripts/run_local_advisor.py`
3. **Run the tests** → Run `python3 -m pytest tests/test_advisor.py -v`
4. **Integrate with workflows** → Follow AI_ADVISOR_INTEGRATION.md
5. **Test end-to-end** → Follow TESTING_WORKFLOW.md

---

## 🎯 Success Criteria

✅ Unit tests: 12/12 passing
✅ Local advisor: All 5 scenarios working
✅ Integration: PR comments posting correctly
✅ Degradation: Pipeline works without API key
✅ Cost: <$0.05 per PR
✅ Latency: <5s additional per gate
✅ Documentation: Complete and tested

---

## 📞 Getting Help

1. **Understanding design** → See ADVISORY_ARCHITECTURE.md
2. **Integrating with CI/CD** → See AI_ADVISOR_INTEGRATION.md
3. **Testing scenarios** → See TESTING_WORKFLOW.md
4. **Troubleshooting** → See docs/TESTING_WORKFLOW.md#Troubleshooting

---

## 🚀 Next Phase

Ready for:
- [ ] GitHub Secrets configuration
- [ ] Gate 1/2/3 workflow updates
- [ ] End-to-end testing with real PRs
- [ ] Performance monitoring
- [ ] Developer feedback collection

Status: **Implementation Complete** ✅ → **Integration Ready** 🚀

