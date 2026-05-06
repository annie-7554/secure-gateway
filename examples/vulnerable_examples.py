"""Example vulnerable code for testing the security advisor.

These are intentionally vulnerable examples for testing scanning
and advisory workflows.
"""


# Example 1: SQL Injection Vulnerability
# Detectable by: Semgrep, SQLMap
def vulnerable_query(user_id):
    """Intentionally vulnerable SQL query - DO NOT use in production."""
    import sqlite3
    conn = sqlite3.connect(":memory:")
    
    # VULNERABLE: SQL injection - user_id not parameterized
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor = conn.execute(query)
    return cursor.fetchall()


# Example 2: Hardcoded Secret
# Detectable by: TruffleHog, GitGuardian
# This would be caught by TruffleHog scanning commit history
VULNERABLE_API_KEY = "sk_live_51234567890abcdefghijklmnop"
VULNERABLE_DATABASE_PASSWORD = "super_secret_password_123"


# Example 3: Insecure Cryptography
# Detectable by: Semgrep
def vulnerable_password_hash(password):
    """Intentionally using weak hashing - DO NOT use in production."""
    import hashlib
    
    # VULNERABLE: MD5 is cryptographically broken
    return hashlib.md5(password.encode()).hexdigest()


# Example 4: Insecure Deserialization
# Detectable by: Semgrep
def vulnerable_deserialize(data):
    """Intentionally using insecure deserialization - DO NOT use."""
    import pickle
    
    # VULNERABLE: Pickle can execute arbitrary code
    return pickle.loads(data)


# Example 5: Path Traversal
# Detectable by: Semgrep
def vulnerable_file_read(filename):
    """Intentionally vulnerable file read - DO NOT use in production."""
    # VULNERABLE: No validation of filename parameter
    with open(f"/uploads/{filename}", "r") as f:
        return f.read()


if __name__ == "__main__":
    print("These are vulnerable examples for testing only!")
    print("See test cases in examples/ for usage.")
