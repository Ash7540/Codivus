import ast
from typing import List
from codereview.models import Issue, Suggestion

class FormattingVisitor(ast.NodeVisitor):
    def __init__(self, source_lines: List[str], max_func_lines: int = 50, max_methods: int = 10):
        self.source_lines = source_lines
        self.max_func_lines = max_func_lines
        self.max_methods = max_methods
        self.issues: List[Issue] = []

    def visit_FunctionDef(self, node):
        self._check_function_length(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self._check_function_length(node)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self._check_class_complexity(node)
        self.generic_visit(node)

    def _check_function_length(self, node):
        end_lineno = getattr(node, "end_lineno", node.lineno)
        total_lines = end_lineno - node.lineno + 1
        
        if total_lines > self.max_func_lines:
            lineno = node.lineno
            snippet = self.source_lines[lineno - 1] if 0 < lineno <= len(self.source_lines) else ""
            self.issues.append(Issue(
                title="Overly Long Function",
                description=(
                    f"Function/method '{node.name}' spans {total_lines} lines, which exceeds "
                    f"the recommended maximum length of {self.max_func_lines} lines. "
                    "Long functions are harder to read, maintain, and test."
                ),
                severity="medium",
                category="style",
                line_number=lineno,
                code_snippet=snippet.strip(),
                suggestion=Suggestion(
                    original_code=snippet,
                    proposed_code=f"# Consider refactoring {node.name} into helper functions.",
                    explanation="Refactoring long functions into smaller, single-responsibility functions increases readability and testability."
                )
            ))

    def _check_class_complexity(self, node):
        methods = 0
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not child.name.startswith("_") or child.name == "__init__":
                    methods += 1
                    
        if methods > self.max_methods:
            lineno = node.lineno
            snippet = self.source_lines[lineno - 1] if 0 < lineno <= len(self.source_lines) else ""
            self.issues.append(Issue(
                title="Overly Complex Class Design",
                description=(
                    f"Class '{node.name}' has {methods} public methods, which exceeds "
                    f"the recommended threshold of {self.max_methods} methods. "
                    "Classes with too many methods often violate the Single Responsibility Principle."
                ),
                severity="low",
                category="style",
                line_number=lineno,
                code_snippet=snippet.strip(),
                suggestion=Suggestion(
                    original_code=snippet,
                    proposed_code=f"# Consider extracting logic from class {node.name} into helper classes.",
                    explanation="Keeping classes focused on a single responsibility prevents bloating and simplifies unit testing."
                )
            ))

def detect_formatting_violations(tree: ast.AST, source_lines: List[str]) -> List[Issue]:
    visitor = FormattingVisitor(source_lines)
    visitor.visit(tree)
    return visitor.issues
