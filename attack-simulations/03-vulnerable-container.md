# VULNERABLE CONTAINER IMAGE - Caught by Trivy
# This demonstrates container image vulnerabilities

# ❌ VULNERABLE DOCKERFILE (DO NOT USE)
"""
FROM ubuntu:20.04          # ← Too many packages, outdated
RUN apt-get install -y \\
    curl wget openssh-server \\
    git vim build-essential \\
    apache2 mysql-client    # ← Unnecessary packages
RUN useradd -m appuser
COPY . /app
EXPOSE 22                  # ← SSH exposed
RUN apt-get clean
ENTRYPOINT ["/bin/bash"]   # ← Root shell access!
"""

# VULNERABILITIES IN THIS IMAGE:
"""
TRIVY SCAN RESULTS:
──────────────────────────────────────────────────────
✗ CRITICAL - OpenSSH Server CVE-2021-41617
  Package: openssh-server:1:8.2p1-4
  Available Fix: 1:8.2p1-4ubuntu0.5

✗ HIGH - Apache HTTP Server CVE-2021-44790
  Package: apache2:2.4.41-1ubuntu1.10
  Available Fix: 2.4.41-1ubuntu1.13

✗ HIGH - Bash CVE-2021-4034 (PwnKit)
  Package: bash:5.0-1ubuntu1.1
  Available Fix: 5.0-1ubuntu1.1ubuntu0.1

✗ MEDIUM - Git CVE-2022-24765
  Package: git:1:2.25.1-1ubuntu3
  Available Fix: 1:2.37.0-1ubuntu1
──────────────────────────────────────────────────────
Total: 47 vulnerabilities found (15 CRITICAL, 24 HIGH)
"""

# ATTACK SCENARIOS:

# 1. PRIVILEGE ESCALATION
"""
ATTACK: Container runs as root
  - Any code execution → Full container compromise
  - Kernel exploits possible
  - Ability to modify system binaries
  - Can write to /etc/passwd for persistent access
"""

# 2. SSH BACKDOOR
"""
ATTACK: OpenSSH exposed in container
  - Port 22 accessible to network
  - Brute force attacks
  - If compromised, attacker has shell
  - Can be used to pivot to other containers
"""

# 3. UNNECESSARY PACKAGES
"""
ATTACK: Unnecessary packages = unnecessary vulnerabilities
  - Apache2 not used → CVEs in Apache benefit attacker
  - MySQL client not needed → SQL injection tools included
  - vim/git → Text editor vulnerabilities
  - build-essential → Attacker can compile malware
"""

# ====================
# HOW TRIVY WORKS
# ====================

"""
TRIVY SCANNING PROCESS:
1. Extract filesystem from image (or scan running container)
2. Identify OS packages (apt, yum, apk, etc.)
3. Look up installed package versions
4. Query NVD/CVE databases for vulnerabilities
5. Generate SARIF report with findings
6. Fail pipeline if vulnerabilities meet threshold

TRIVY OUTPUT:
docker run aquasec/trivy image myapp:latest

  myapp:latest (ubuntu 20.04)
  ─────────────────────────────────
  Total: 47 (CRITICAL: 15, HIGH: 24, MEDIUM: 8)
"""


# ====================
# ✅ SECURE DOCKERFILE
# ====================

"""
FROM python:3.11-slim          # ← Minimal base image (4x smaller)

# Non-root user (prevents privilege escalation)
RUN useradd -r -g appuser appuser

# Only necessary packages
RUN apt-get update && apt-get install -y --no-install-recommends \\
    curl \\
    && rm -rf /var/lib/apt/lists/*  # ← Remove package cache (saves space + CVEs)

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .
RUN chown -R appuser:appuser /app

USER appuser  # ← Switch to non-root

EXPOSE 8000  # ← Application port only (not SSH)
HEALTHCHECK --interval=30s CMD curl -f http://localhost:8000/health

ENTRYPOINT ["python", "-u", "app.py"]  # ← Application, not shell
"""

# TRIVY SCAN RESULTS FOR SECURE IMAGE:
"""
devsecops-app:latest (debian 12.1)
──────────────────────────────────────
Total: 2 (CRITICAL: 0, HIGH: 0, MEDIUM: 2, LOW: 0)

✓ PASS - No critical/high vulnerabilities
✓ PASS - Image size: 140MB (vs 350MB for vulnerable ubuntu image)
✓ PASS - Non-root user enforced
"""

# ====================
# SBOM (Software Bill of Materials)
# ====================

"""
SBOM lists every package in container:
- Python 3.11.6
  - pip 24.0.1
  - setuptools 68.0.0
  - Flask 2.3.3
  - Werkzeug 2.3.7
  - ...

USE CASES:
1. Audit: Know exactly what's in your container
2. Compliance: Demonstrate supply chain security
3. Incident response: If critical CVE found, know which containers affected
4. License compliance: Identify GPL/proprietary licenses

SYFT COMMAND:
syft devsecops-app:latest -o spdx-json > sbom.spdx.json
"""
