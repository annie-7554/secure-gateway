# Demo vulnerable SQL code (for Semgrep demo)

def get_user(db, username):
    # Unsafe: direct string formatting into SQL
    query = "SELECT * FROM users WHERE username = '%s'" % username
    print("Executing:", query)
    return db.execute(query)

