# VULNERABLE CODE EXAMPLE - Caught by Semgrep SAST
# This demonstrates SQL injection - a critical vulnerability that Semgrep detects

# ❌ VULNERABLE VERSION (DO NOT USE)
import sqlite3

def login_vulnerable(username, password):
    """
    VULNERABLE: Direct string concatenation in SQL query
    An attacker can input: admin' OR '1'='1
    This bypasses authentication by modifying the SQL logic
    """
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Semgrep will flag this as sql-injection
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)  # ❌ VULNERABLE
    
    return cursor.fetchone() is not None


# ✅ SECURE VERSION (What Semgrep recommends)
def login_secure(username, password):
    """
    SECURE: Parameterized query prevents SQL injection
    The database driver handles escaping, ensuring user input is treated as data, not code
    """
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Semgrep approves this pattern
    query = "SELECT * FROM users WHERE username=? AND password=?"
    cursor.execute(query, (username, password))  # ✅ SECURE
    
    return cursor.fetchone() is not None


# ====================
# ATTACK EXPLANATION
# ====================

"""
ATTACK: SQL Injection
IMPACT: High - Complete database compromise

VULNERABLE ATTACK PAYLOAD:
  username: admin' --
  password: anything
  
RESULTING QUERY:
  SELECT * FROM users WHERE username='admin' --' AND password='anything'
  
THE COMMENT (--) IGNORES THE PASSWORD CHECK → Login bypassed!

HOW SEMGREP CATCHES THIS:
- Detects f-strings/format() in SQL queries
- Flags string concatenation with user input
- Recommends parameterized queries

FIX:
- Always use ? placeholders (sqlite3) or %s (psycopg2)
- Let database driver handle escaping
- Never concatenate user input into SQL
"""
