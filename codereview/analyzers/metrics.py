from typing import List
from codereview.analyzers.base import BaseAnalyzer
from codereview.models import Issue, CodeContext


class MetricsAnalyzer(BaseAnalyzer):
    def __init__(self, min_density: float = 0.05, max_functions: int = 15):
        self.min_density = min_density
        self.max_functions = max_functions

    def analyze(self, context: CodeContext) -> List[Issue]:
        issues = []
        stats = context.stats

        # Calculate comment density relative to source code + comments
        total_non_blank = stats.loc + stats.comment_lines
        density = stats.comment_lines / total_non_blank if total_non_blank > 0 else 0.0

        if stats.loc > 20 and density < self.min_density:
            issues.append(
                Issue(
                    title="Low Comment Density",
                    description=(
                        f"The file has a low comment density of {density:.1%} "
                        f"(recommended at least {self.min_density:.0%}). "
                        f"Adding explanations and docstrings helps developers understand intent."
                    ),
                    severity="low",
                    category="style",
                    line_number=1,
                    code_snippet="",
                    suggestion=None,
                )
            )

        if stats.num_functions > self.max_functions:
            issues.append(
                Issue(
                    title="High Function Count",
                    description=(
                        f"This file contains {stats.num_functions} functions, which exceeds the "
                        f"recommended maximum of {self.max_functions}. Consider splitting "
                        f"the module into smaller, more focused files."
                    ),
                    severity="low",
                    category="style",
                    line_number=1,
                    code_snippet="",
                    suggestion=None,
                )
            )

        return issues
