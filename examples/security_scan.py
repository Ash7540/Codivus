import os
from codereview.config import Config
from codereview.reviewer import Reviewer

def main():
    print("=== Custom Security Audit Focus ===")
    
    # 1. Setup insecure dummy script
    insecure_code = """
import sqlite3

def login_user(username, password):
    # Security Bug: SQL injection vulnerability
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    return cursor.fetchone()

def get_admin_key():
    # Security Bug: Hardcoded credentials
    secret_token = "SUPER_SECRET_ADMIN_TOKEN_12345"
    return secret_token
"""
    temp_file = "temp_insecure_code.py"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(insecure_code.strip())
        
    print(f"Created temporary target '{temp_file}' containing security flaws.")

    try:
        # 2. Setup reviewer using mock provider
        config = Config(overrides={"default_provider": "mock"})
        reviewer = Reviewer(config)
        
        # 3. Run audit focusing solely on security issues
        print("Auditing file with security category focus...")
        result = reviewer.review_file(temp_file, category_focus="security")
        
        # 4. Display findings
        print(f"Security quality score: {result.score.security_score}/100")
        print(f"Security issues identified: {len(result.issues)}")
        for idx, issue in enumerate(result.issues, start=1):
            print(f"[{issue.severity.upper()}] Issue #{idx}: {issue.title}")
            print(f"  Description: {issue.description}")
            
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"Cleaned up temporary target '{temp_file}'.")

if __name__ == "__main__":
    main()
