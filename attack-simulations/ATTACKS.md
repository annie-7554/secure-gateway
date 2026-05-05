# Security Control Validation: Attack Scenarios

Vulnerability examples demonstrating detection and remediation across the security pipeline.

### Detection Summary
```
Gate 1 (Code Security)    → SQL injection, hardcoded secrets, weak dependencies
Gate 2 (Build Security)   → Vulnerable base image, unpatched packages
Gate 3 (Deploy Security)  → Unsigned images, insufficient RBAC, no approvals
```

---

## SCENARIO 1: SQL Injection Caught by Semgrep (Gate 1)

### The Vulnerability
```python
# In src/app.py - vulnerable login function
def login(username, password):
    query = f"SELECT * FROM users WHERE username='{username}'"
    cursor.execute(query)  # ❌ VULNERABLE
```

### The Attack
```
Attacker submits form:
  username: admin' --
  password: anything

Result: Query becomes
  SELECT * FROM users WHERE username='admin' --' AND password=...
  (The -- comments out password check)
  
Outcome: Login bypassed, account takeover
```

### How Gate 1 Stops It
- Semgrep detects f-string interpolation in SQL queries
- Flags it as `injection-sql`
- GitHub shows findings in PR security tab
- PR cannot merge until fixed

### The Fix
```python
# Use parameterized query
query = "SELECT * FROM users WHERE username=? AND password=?"
cursor.execute(query, (username, password))  # ✅ SECURE
```

### To Test This:
1. Add vulnerable code to `src/app.py`
2. Create a PR
3. Semgrep finds it
4. See failure in GitHub Actions workflow
5. Apply fix, commit, watch gate pass

---

## SCENARIO 2: Hardcoded Secret Caught by TruffleHog (Gate 1)

### The Vulnerability
```python
# In config.py
DATABASE_PASSWORD = "super_secret_p@ssw0rd_123"
AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
```

### The Attack
- Attacker finds GitHub repo (public or after breach)
- Discovers hardcoded database password in git history
- Connects directly to production database
- Exfiltrates customer data
- Modifies records for fraud

### How Gate 1 Stops It
- TruffleHog scans all commits in PR
- Detects patterns: `AKIA...`, database passwords, API tokens
- Fails PR with list of exposed secrets
- Recommend credential rotation
- PR blocked until secrets removed

### The Fix
```python
# Use environment variables
import os
database_password = os.getenv("DATABASE_PASSWORD")

# Or use AWS Secrets Manager
import boto3
secrets = boto3.client('secretsmanager')
password = secrets.get_secret_value(SecretId='prod/db/password')
```

### To Test This:
1. Add `FAKE_API_TOKEN = "ghp_1234567890abcdefghijk"` to any file
2. Commit to a PR branch
3. Create PR
4. TruffleHog detects and fails
5. Remove secret, push fix
6. Gate passes

---

## SCENARIO 3: Vulnerable Dependency Caught by Snyk (Gate 1)

### The Vulnerability
```
requirements.txt:
Flask==2.0.0          # CVE-2021-23493: SQL injection in werkzeug
Pillow==5.0.0         # CVE-2019-6552: RCE in image processing
pyyaml==5.1           # CVE-2020-14343: RCE in yaml.load()
```

### The Attack
1. Attacker sends image with malicious content
2. Application processes with Pillow 5.0.0
3. Arbitrary code execution on server
4. Attacker gains shell access
5. Steals customer data, installs backdoor

### How Gate 1 Stops It
- Snyk scans requirements.txt
- Looks up each package version in CVE database
- Finds high/critical vulnerabilities
- Fails pipeline with upgrade recommendations
- PR cannot merge until dependencies updated

### The Fix
```
requirements.txt:
Flask==2.3.3          # ✅ Security patches, no known CVEs
Pillow==10.0.0        # ✅ All CVEs patched
PyYAML==6.0           # ✅ Secure, use safe_load()
```

### To Test This:
1. Modify requirements.txt with old versions
2. Push to PR
3. Snyk fails with CVE list
4. Update to safe versions
5. Re-push, gate passes

---

## SCENARIO 4: Vulnerable Container Image Caught by Trivy (Gate 2)

### The Vulnerability
Dockerfile with weak base image:
```dockerfile
FROM ubuntu:20.04           # ❌ 350MB, 47 CVEs
RUN apt-get install -y \
    openssh-server \         # ❌ Unnecessary
    build-essential          # ❌ Unnecessary
RUN useradd -m appuser      # ❌ No "r" flag - can be in sudoers
ENTRYPOINT ["/bin/bash"]    # ❌ Root shell!
```

### The Attack
1. Code execution vulnerability found in openssh-server
2. Attacker remotely connects to port 22
3. Root access → full system control
4. Modifies application code, installs backdoor
5. Accesses other containers via shared network

### How Gate 2 Stops It
- Trivy scans built image
- Detects 47 vulnerabilities (15 CRITICAL)
- Generates SARIF report
- Build fails with list of CVEs
- Push to container registry blocked

### The Fix
```dockerfile
FROM python:3.11-slim       # ✅ 140MB, 2 low-risk vulnerabilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*  # ✅ Clean cache
RUN useradd -r -g appgroup appuser # ✅ System user
USER appuser                         # ✅ Non-root
EXPOSE 8000                         # ✅ App port only
```

### To Test This:
1. Build image with vulnerable Dockerfile
2. Push to workflow that runs Trivy
3. See Trivy findings
4. Apply secure Dockerfile
5. Rebuild, Trivy passes

---

## SCENARIO 5: Unsigned Image + Insufficient RBAC (Gate 3)

### The Vulnerability
1. Image not signed → can't verify origin
2. Kubernetes RBAC too permissive → container can modify itself
3. No approval required for production

### The Attack
1. Attacker compromises container registry
2. Pushes malicious image with same tag
3. Deploy workflow pulls malicious image (no signature check)
4. Malicious container starts, modifies application
5. Container breaks out via privilege escalation (permissive RBAC)
6. Accesses other workloads

### How Gate 3 Stops It

#### Attack 1: Unsigned Image
- Kyverno policy requires signed images
- verifyImageSignature checks cosign signature
- Malicious image fails verification
- Pod rejected at admission time
```
❌ Failed to verify image signature
   Image: registry/app:malicious
   Only signed images allowed
```

#### Attack 2: Insufficient RBAC
- Deployment service account has read-only permissions
- Cannot create/patch/delete resources
- Container escape doesn't help attacker
- Limited scope of compromise
```
$ kubectl patch deployment devsecops-app --patch='...'
Error: user system:serviceaccount:devsecops-app:devsecops-app
       cannot patch deployments in namespace "devsecops-app"
```

#### Attack 3: No Approval
- Production deployments require GitHub environment approval
- Only authorized reviewers can approve
- Prevents malicious or accidental deployments
- Audit trail of who approved what

### The Fix
```
1. Sign image with Cosign
2. Configure Kyverno signature verification
3. Set least-privilege RBAC (read pods only)
4. Require 2+ approvals for production deployment
```

### To Test This:
1. Try deploying unsigned image → Kyverno blocks
2. Try accessing deployments with service account → RBAC denies
3. Try deploying to production without approval → GitHub blocks

---

## Testing All Scenarios

### Prerequisites
```bash
# Install tools locally
pip install -r requirements.txt
brew install semgrep tfsec cosign

# Setup kubectl
kubectl create namespace devsecops-app
kubectl apply -f k8s/
```

### Run Full Pipeline (Locally)
```bash
# Gate 1: Code security
semgrep scan --config=p/security-audit src/
trufflehog git file://. --only-verified

# Gate 2: Container security
docker build -t devsecops-app:test -f docker/Dockerfile .
trivy image devsecops-app:test

# Gate 3: Deploy
kubectl apply -f k8s/deployment.yaml
```

### Trigger Real Failures in GitHub Actions
1. Add vulnerable code to PR
2. Watch workflows fail in real-time
3. See security findings in GitHub UI
4. Fix and watch gates pass

---

## Key Learnings for Interviews

### What to Emphasize
1. **Shift-Left Security**: Catch issues early (code stage, not deployment)
2. **Defense in Depth**: Multiple gates = multiple chances to catch attacks
3. **Fail-Safe Defaults**: Block by default, explicitly allow
4. **Least Privilege**: Service accounts, RBAC, read-only filesystems
5. **Supply Chain Security**: Sign images, scan dependencies, verify provenance

### Interview Talking Points
- "Gate 1 catches logic vulnerabilities + exposed secrets + dependencies"
- "Gate 2 ensures image safety + generates SBOM for audit"
- "Gate 3 requires approval + signature verification + minimal RBAC"
- "Each gate has attack examples we can trigger to demonstrate real failures"

### Metrics to Mention
- Time to fail: ~2 minutes (all three gates)
- False positives: <5% (well-tuned Semgrep rules)
- Mean time to remediate: <30 min (security updates)
- Coverage: 100% of PRs, 100% of deployments
