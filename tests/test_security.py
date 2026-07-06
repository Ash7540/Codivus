import pytest
import ast
from codereview.models import CodeContext, FileStats
from codereview.parsers.python import PythonParser
from codereview.security.scanner import SecurityAnalyzer

def test_sql_injection_detection():
    code = """
def run_queries(user_input):
    # Vulnerable: directly using f-string
    cursor.execute(f"SELECT * FROM users WHERE name = '{user_input}'")
    
    # Vulnerable: string concatenation
    cursor.execute("SELECT * FROM users WHERE name = '" + user_input + "'")
    
    # Vulnerable: format method
    cursor.executemany("SELECT * FROM users WHERE name = '{}'".format(user_input))
    
    # Vulnerable: % formatting
    cursor.executescript("SELECT * FROM users WHERE name = '%s'" % user_input)
    
    # Vulnerable: variable assignment and pass
    sql_query = f"SELECT * FROM users WHERE name = '{user_input}'"
    cursor.execute(sql_query)
    
    # Safe query
    cursor.execute("SELECT * FROM users WHERE name = ?", (user_input,))
"""
    parser = PythonParser()
    context = parser.parse_code(code, "db.py")
    analyzer = SecurityAnalyzer()
    issues = analyzer.analyze(context)
    
    sql_issues = [i for i in issues if i.title == "Potential SQL Injection"]
    
    # Should detect 5 SQL injection instances (direct f-string, concat, format, %, and variable tracing)
    assert len(sql_issues) == 5
    for issue in sql_issues:
        assert issue.severity == "critical"
        assert issue.category == "security"

def test_subprocess_and_command_injection():
    code = """
import os
import subprocess
from commands import getoutput

def run_commands(user_path):
    # Vulnerable: os.system with dynamic string
    os.system("ls -la " + user_path)
    
    # Vulnerable: os.popen with dynamic string
    os.popen(f"cat {user_path}")
    
    # Vulnerable: subprocess with shell=True and dynamic string
    subprocess.run(f"rm -rf {user_path}", shell=True)
    
    # Vulnerable: subprocess with shell=True (static string)
    subprocess.Popen("echo 'hello'", shell=True)
    
    # Safe subprocess
    subprocess.run(["ls", "-la", user_path])
"""
    parser = PythonParser()
    context = parser.parse_code(code, "proc.py")
    analyzer = SecurityAnalyzer()
    issues = analyzer.analyze(context)
    
    proc_issues = [i for i in issues if i.title in ("Unsafe Process Execution", "Unsafe Subprocess with shell=True")]
    
    assert len(proc_issues) == 4
    
    # Check severity
    # subprocess.run(..., shell=True) with dynamic string -> critical
    critical_sub = next(i for i in proc_issues if "subprocess.run" in i.description and i.severity == "critical")
    assert "shell=True" in critical_sub.description
    
    # subprocess.Popen("...", shell=True) with static string -> high
    high_sub = next(i for i in proc_issues if "subprocess.Popen" in i.description and i.severity == "high")
    assert "shell=True" in high_sub.description

def test_hardcoded_secrets():
    code = f"""
# Critical: AWS key signature
MY_AWS_KEY = "AK{"IA1234567890ABCDEF"}"

# Critical: Slack token signature
SLACK_API_TOKEN = "xo{"xb-1234567890-abcdefghijklmnop"}"

# High:Credential name + high entropy string
DB_PASSWORD = "superSecretPassword123!"

# Safe: Placeholder patterns
API_KEY = "your_api_key"
pass_word = "PLACEHOLDER"
empty_token = ""
"""
    parser = PythonParser()
    context = parser.parse_code(code, "config.py")
    analyzer = SecurityAnalyzer()
    issues = analyzer.analyze(context)
    
    secret_issues = [i for i in issues if "Hardcoded" in i.title]
    
    assert len(secret_issues) == 3
    
    aws_issue = next(i for i in secret_issues if "AWS" in i.title)
    assert aws_issue.severity == "critical"
    assert "AKIA**************EF" in aws_issue.description  # Must be masked

    
    slack_issue = next(i for i in secret_issues if "Slack" in i.title)
    assert slack_issue.severity == "critical"
    
    pw_issue = next(i for i in secret_issues if "Secret/Credential" in i.title)
    assert pw_issue.severity == "high"

def test_eval_exec_injection():
    code = """
def process(user_input):
    # Critical: dynamic eval
    eval(user_input)
    
    # High: static exec
    exec("print('hello')")
    
    # Safe: literal eval
    import ast
    ast.literal_eval("[1, 2, 3]")
"""
    parser = PythonParser()
    context = parser.parse_code(code, "eval_test.py")
    analyzer = SecurityAnalyzer()
    issues = analyzer.analyze(context)
    
    eval_issues = [i for i in issues if "Dangerous Use of" in i.title]
    
    assert len(eval_issues) == 2
    
    eval_node = next(i for i in eval_issues if "eval" in i.title)
    assert eval_node.severity == "critical"
    
    exec_node = next(i for i in eval_issues if "exec" in i.title)
    assert exec_node.severity == "high"

def test_weak_cryptography():
    code = """
import hashlib
from cryptography.hazmat.primitives.ciphers.modes import ECB
from cryptography.hazmat.primitives.ciphers.algorithms import DES

def hash_pass(data):
    # Medium: hashlib weak hashes
    h1 = hashlib.md5(data)
    h2 = hashlib.sha1(data)
    
    # Safe hashing
    h3 = hashlib.sha256(data)
"""
    parser = PythonParser()
    context = parser.parse_code(code, "crypto.py")
    analyzer = SecurityAnalyzer()
    issues = analyzer.analyze(context)
    
    crypto_issues = [i for i in issues if "Cryptographic" in i.title]
    
    # Should detect:
    # 1. md5 call (medium)
    # 2. sha1 call (medium)
    # 3. Import ECB (high)
    # 4. Import DES (high)
    assert len(crypto_issues) == 4
    
    hash_issues = [i for i in crypto_issues if "Hash Function" in i.title]
    assert len(hash_issues) == 2
    for issue in hash_issues:
        assert issue.severity == "medium"
        
    import_issues = [i for i in crypto_issues if "Imported" in i.title]
    assert len(import_issues) == 2
    for issue in import_issues:
        assert issue.severity == "high"

def test_xss_autoescape():
    code = """
from jinja2 import Environment, FileSystemLoader

# High: Autoescape disabled
env_unsafe = Environment(
    loader=FileSystemLoader('templates'),
    autoescape=False
)

# Safe: Autoescape enabled
env_safe = Environment(
    loader=FileSystemLoader('templates'),
    autoescape=True
)
"""
    parser = PythonParser()
    context = parser.parse_code(code, "web.py")
    analyzer = SecurityAnalyzer()
    issues = analyzer.analyze(context)
    
    xss_issues = [i for i in issues if i.title == "Jinja2 Autoescape Disabled"]
    assert len(xss_issues) == 1
    assert xss_issues[0].severity == "high"
