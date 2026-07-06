import ast
import re
import math
from typing import List
from codereview.models import Issue, Suggestion

# Common variable name patterns that store secrets
SECRET_VAR_PATTERNS = re.compile(
    r'(key|secret|password|passwd|token|private_?key|auth|credential|db_?pass|passphrase)',
    re.IGNORECASE
)

# Common generic values to ignore (case-insensitive)
IGNORE_PLACEHOLDERS = {
    "", "your_api_key", "your_secret", "your_password", "password", "secret", "token", "null", "none",
    "todo", "change_me", "changeme", "placeholder", "dummy", "test", "mysecret", "db_password", "user_password"
}

# AWS Access Key ID regex: AKIA / ASIA followed by 16 uppercase alphanumerics
AWS_KEY_PATTERN = re.compile(r'\b(AKIA|ASIA)[0-9A-Z]{16}\b')

# Slack Token pattern
SLACK_TOKEN_PATTERN = re.compile(r'\bxox[bapr]-[0-9a-zA-Z]{10,48}\b')

def shannon_entropy(data: str) -> float:
    if not data:
        return 0.0
    entropy = 0.0
    for x in set(data):
        p_x = float(data.count(x)) / len(data)
        entropy -= p_x * math.log2(p_x)
    return entropy

class SecretsVisitor(ast.NodeVisitor):
    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.issues: List[Issue] = []

    def visit_Assign(self, node):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                val = node.value.value
                is_secret_var = SECRET_VAR_PATTERNS.search(var_name) is not None
                self._check_secret_value(var_name, val, node.lineno, is_secret_var)
        self.generic_visit(node)

    def _check_secret_value(self, var_name: str, val: str, lineno: int, is_secret_var: bool):
        val_lower = val.lower().strip()
        
        # 1. Ignore placeholders and short strings
        if val_lower in IGNORE_PLACEHOLDERS or len(val) < 6:
            return
            
        # 2. Check for known pattern signatures
        is_pattern_match = False
        sig_name = ""
        
        if AWS_KEY_PATTERN.search(val):
            is_pattern_match = True
            sig_name = "AWS Access Key ID"
        elif SLACK_TOKEN_PATTERN.search(val):
            is_pattern_match = True
            sig_name = "Slack Token"
            
        # If pattern matched, or it is a credential variable name with high entropy
        if is_pattern_match or (is_secret_var and shannon_entropy(val) > 3.0 and len(val) >= 8):
            severity = "critical" if is_pattern_match else "high"
            title = f"Hardcoded {sig_name if is_pattern_match else 'Secret/Credential'}"
            
            snippet = self.source_lines[lineno - 1] if 0 < lineno <= len(self.source_lines) else ""
            
            # Mask the secret securely
            masked_val = val[:4] + "*" * (len(val) - 6) + val[-2:] if len(val) > 6 else "****"
            
            self.issues.append(Issue(
                title=title,
                description=(
                    f"Possible hardcoded credential or secret '{masked_val}' assigned to variable '{var_name}'. "
                    "Storing raw secrets in source code poses significant security risks. "
                    "Use environment variables or a secret management service instead."
                ),
                severity=severity,
                category="security",
                line_number=lineno,
                code_snippet=snippet.strip(),
                suggestion=Suggestion(
                    original_code=snippet,
                    proposed_code=f"import os\n{var_name} = os.getenv(\"{var_name.upper()}\")",
                    explanation="Using environment variables keeps credentials out of the codebase and prevents accidental exposure."
                )
            ))


def detect_hardcoded_secrets(tree: ast.AST, source_lines: List[str]) -> List[Issue]:
    visitor = SecretsVisitor(source_lines)
    visitor.visit(tree)
    return visitor.issues
