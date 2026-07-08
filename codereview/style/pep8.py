import ast
from typing import List
from codereview.analyzers.base import BaseAnalyzer
from codereview.models import Issue, CodeContext

from codereview.style.naming import detect_naming_violations
from codereview.style.comments import detect_missing_comments
from codereview.style.formatting import detect_formatting_violations
from codereview.style.best_practices import detect_best_practice_violations

class StyleAnalyzer(BaseAnalyzer):
    def analyze(self, context: CodeContext) -> List[Issue]:
        issues: List[Issue] = []
        try:
            tree = ast.parse(context.source_code)
        except Exception:
            # Syntax/structure errors are handled by other analyzers
            return []

        source_lines = context.source_code.splitlines()

        # Run all style analysis rule checkers
        issues.extend(detect_naming_violations(tree, source_lines))
        issues.extend(detect_missing_comments(tree, source_lines))
        issues.extend(detect_formatting_violations(tree, source_lines))
        issues.extend(detect_best_practice_violations(tree, source_lines))

        return issues
