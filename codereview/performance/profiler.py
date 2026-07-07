import ast
from typing import List
from codereview.analyzers.base import BaseAnalyzer
from codereview.models import Issue, CodeContext

from codereview.performance.loops import detect_loop_inefficiencies
from codereview.performance.memory import detect_memory_inefficiencies
from codereview.performance.asynchronous import detect_async_misuse
from codereview.performance.optimisation import detect_redundant_operations


class PerformanceAnalyzer(BaseAnalyzer):
    def analyze(self, context: CodeContext) -> List[Issue]:
        issues: List[Issue] = []
        try:
            tree = ast.parse(context.source_code)
        except Exception:
            # Syntax/structure errors are handled by other analyzers
            return []

        source_lines = context.source_code.splitlines()

        # Run all performance analysis rule checkers
        issues.extend(detect_loop_inefficiencies(tree, source_lines))
        issues.extend(detect_memory_inefficiencies(tree, source_lines))
        issues.extend(detect_async_misuse(tree, source_lines))
        issues.extend(detect_redundant_operations(tree, source_lines))

        return issues
