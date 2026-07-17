import ast
from typing import List
from codereview.analyzers.base import BaseAnalyzer
from codereview.models import Issue, Suggestion, CodeContext


class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.complexity = 1

    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_IfExp(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_And(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_Or(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        # Stop traversal so nested functions are not aggregated
        pass

    def visit_AsyncFunctionDef(self, node):
        # Stop traversal so nested functions are not aggregated
        pass

    def visit_ClassDef(self, node):
        # Stop traversal so nested classes are not traversed
        pass


class ComplexityAnalyzer(BaseAnalyzer):
    def __init__(self, threshold: int = 10):
        self.threshold = threshold

    def analyze(self, context: CodeContext) -> List[Issue]:
        issues = []
        try:
            tree = ast.parse(context.source_code)
        except Exception:
            # If parse fails, it is handled elsewhere
            return []

        # Find all functions (module level and class level)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Calculate complexity for this specific function
                visitor = ComplexityVisitor()
                # Manually traverse children of the function node (skipping the function node itself so visitor doesn't block immediately)
                for child in node.body:
                    visitor.visit(child)

                complexity = visitor.complexity

                # Check threshold
                if complexity > self.threshold:
                    severity = "high" if complexity > 15 else "medium"

                    # Extract the definition line for code snippet
                    lines = context.source_code.splitlines()
                    snippet = (
                        lines[node.lineno - 1] if 0 < node.lineno <= len(lines) else ""
                    )

                    issues.append(
                        Issue(
                            title="High Cyclomatic Complexity",
                            description=(
                                f"Function '{node.name}' has a cyclomatic complexity of {complexity}, "
                                f"which exceeds the recommended threshold of {self.threshold}. "
                                f"High complexity makes functions harder to read, maintain, and test."
                            ),
                            severity=severity,
                            category="style",
                            line_number=node.lineno,
                            code_snippet=snippet.strip(),
                            suggestion=Suggestion(
                                original_code=snippet,
                                proposed_code=f"# Consider refactoring {node.name} into smaller helper functions.",
                                explanation="Refactoring high-complexity functions increases maintainability and readability.",
                            ),
                        )
                    )

        return issues
