# HARDCODED SECRET EXAMPLE - Caught by TruffleHog
# This demonstrates exposed credentials that TruffleHog detects

# ❌ VULNERABLE VERSION (DO NOT USE IN REAL CODE)
# Simulating a file with exposed credentials

AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
DATABASE_PASSWORD = "super_secret_db_password_123"
API_TOKEN = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"

# Configuration that exposes secrets
database_config = {
    "host": "postgres.example.com",
    "user": "admin",
    "password": "MyP@ssw0rd123",  # ❌ Hardcoded password
    "database": "production"
}

# Private key exposed (extremely critical)
PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA2a2rwplBCTwF8EXAMPLE
...
-----END RSA PRIVATE KEY-----"""

# ====================
# TruffleHog Detection
# ====================

"""
WHAT TruffleHog DETECTS:
- AWS key patterns (AKIA.....)
- GitHub tokens (ghp_, ghs_, ghu_)
- Database passwords
- API keys and tokens
- Private cryptographic keys
- Slack tokens, SendGrid keys, etc.

HOW IT WORKS:
1. Scans entire git history
2. Uses regex patterns + entropy detection
3. Cross-references with known leaked key databases
4. Reports findings with commit hash and timestamp

ATTACK IMPACT:
- AWS keys: Full account access, bill fraud, infrastructure compromise
- Database passwords: Complete data breach
- API tokens: Unauthorized access to external services
- Private keys: Code signing abuse, identity theft

EXAMPLE ATTACK:
An attacker finds this file in git history and:
  - Uses AWS keys to spin up mining instances
  - Accesses production database with password
  - Authenticates as the service with API token
  - Signs malicious code with private key

REMEDIATION:
1. IMMEDIATELY rotate credentials
2. Check cloud provider for unauthorized activity
3. Remove from git history (BFG Repo-Cleaner or git filter-branch)
4. Never commit secrets again

PREVENTION:
1. Use environment variables or .env (gitignored)
2. Use secrets management (AWS Secrets Manager, HashiCorp Vault)
3. Use Git pre-commit hooks to scan before committing
4. Add .gitignore rules for .env, config/secrets
5. Use GitHub's built-in Secret Scanning (free for public repos)
"""

# ====================
# ✅ SECURE PATTERNS
# ====================

import os
from dotenv import load_dotenv

# Load secrets from environment (never commit .env)
load_dotenv()

AWS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET = os.getenv("AWS_SECRET_ACCESS_KEY")
DB_PASSWORD = os.getenv("DATABASE_PASSWORD")
API_TOKEN = os.getenv("API_TOKEN")

# Or use a secrets management service
import boto3
secrets_client = boto3.client('secretsmanager')
database_password = secrets_client.get_secret_value(SecretId='prod/db/password')
