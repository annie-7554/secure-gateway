# Vulnerable example: string concatenation leading to SQL injection (demo only)

def get_user(db, username):
    # Unsafe: directly concatenating user input into SQL
    query = "SELECT * FROM users WHERE username = '%s'" % username
    print("Executing:", query)
    return db.execute(query)

# Exploit example: username="' OR '1'='1" will return all users
