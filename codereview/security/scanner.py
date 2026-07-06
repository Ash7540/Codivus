import ast
from typing import List
from codereview.analyzers.base import BaseAnalyzer
from codereview.models import Issue, CodeContext

from codereview.security.sql import detect_sql_injection
from codereview.security.subprocess import detect_subprocess_vulns
from codereview.security.secrets import detect_hardcoded_secrets
from codereview.security.injection import detect_code_injection
from codereview.security.rules import detect_weak_cryptography
from codereview.security.xss import detect_xss_vulns

class SecurityAnalyzer(BaseAnalyzer):
    def analyze(self, context: CodeContext) -> List[Issue]:
        issues: List[Issue] = []
        try:
            tree = ast.parse(context.source_code)
        except Exception:
            # Code structure/syntax issues are handled by other analyzers
            return []

        source_lines = context.source_code.splitlines()

        # Run all security analysis rule checkers
        issues.extend(detect_sql_injection(tree, source_lines))
        issues.extend(detect_subprocess_vulns(tree, source_lines))
        issues.extend(detect_hardcoded_secrets(tree, source_lines))
        issues.extend(detect_code_injection(tree, source_lines))
        issues.extend(detect_weak_cryptography(tree, source_lines))
        issues.extend(detect_xss_vulns(tree, source_lines))

        return issues
