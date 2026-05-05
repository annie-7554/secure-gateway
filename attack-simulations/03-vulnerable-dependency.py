# VULNERABLE DEPENDENCY EXAMPLE - Caught by Snyk/Dependency-Check
# This demonstrates dependencies with known CVEs

# ❌ VULNERABLE VERSION (DO NOT USE)
"""
requirements.txt with vulnerable versions:

Flask==2.0.0          # ← CVE-2021-21342: Werkzeug header injection
Werkzeug==2.0.0       # ← CVE-2021-23343: Upstream url function bypass
requests==2.21.0      # ← Multiple CVEs: proxy auth, SSL verification bypass
Pillow==5.0.0         # ← CVE-2019-6552: Arbitrary code execution
django==2.1.0         # ← 30+ CVEs before 2.2 LTS
pyyaml==5.1           # ← CVE-2020-14343: Arbitrary code execution in load()
"""

# ATTACK EXAMPLE: Vulnerable yaml.load()
import yaml

def parse_config_vulnerable(yaml_string):
    """
    VULNERABLE: yaml.load() executes arbitrary Python code
    Attacker can embed Python that runs during parsing
    """
    return yaml.load(yaml_string)  # ❌ DANGEROUS


# Attack payload:
attack_yaml = """
!!python/object/apply:os.system
args: ['rm -rf / --no-preserve-root']  # Deletes everything!
"""

# If this is parsed: parse_config_vulnerable(attack_yaml)
# → Arbitrary code execution!


# ✅ SECURE VERSION (Use safe_load)
def parse_config_secure(yaml_string):
    """
    SECURE: yaml.safe_load() only deserializes basic Python objects
    Ignores class constructors and arbitrary code execution
    """
    return yaml.safe_load(yaml_string)  # ✅ SAFE


# ====================
# HOW SNYK CATCHES THIS
# ====================

"""
SNYK PROCESS:
1. Reads requirements.txt / package.json / pom.xml
2. Looks up each package version in vulnerability database
3. Checks against known CVEs
4. Calculates severity (Critical/High/Medium/Low)
5. Provides upgrade guidance

EXAMPLE SNYK REPORT:
───────────────────────────────────────────────────────
✗ High severity - Arbitrary Code Execution
  Package: pyyaml
  Installed: 5.1
  Vulnerable: < 5.4
  Fix available: 5.4.1
  CVE: CVE-2020-14343
  
  Description: yaml.load() deserializes untrusted data
  Recommendation: Use yaml.safe_load() or upgrade to 5.4+
───────────────────────────────────────────────────────

ATTACK IMPACT:
- Remote Code Execution (RCE) in dependency parsing
- Application crash/denial of service
- Data theft through backend vulnerabilities
- Supply chain compromise if package is compromised

REAL EXAMPLE (SolarWinds 2020):
- Trusted library had backdoor injected
- Deployed to 18,000+ organizations
- Attackers gained government network access
→ Why supply chain security is critical!

PREVENTION:
1. Regularly update dependencies: pip install --upgrade -r requirements.txt
2. Use semantic versioning: Flask==2.3.* (patch updates only)
3. Use automated tools: Dependabot, Renovate
4. Test thoroughly: Never auto-merge security updates
5. Monitor advisories: GitHub Security Alerts, Snyk
"""

# ====================
# ✅ SECURE DEPENDENCY PINNING
# ====================

"""
✅ BETTER requirements.txt:

# Security-focused versions
Flask==2.3.3          # LTS version with security patches
Werkzeug==2.3.7       # Matches Flask, no known CVEs
Requests==2.31.0      # Latest with security updates
Pillow==10.0.0        # Latest stable
PyYAML==6.0           # Use safe_load only, patched version
"""
