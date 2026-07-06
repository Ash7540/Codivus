import ast
from typing import List
from codereview.models import Issue, Suggestion

class InjectionVisitor(ast.NodeVisitor):
    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.issues: List[Issue] = []

    def visit_Call(self, node):
        is_eval = False
        is_exec = False
        if isinstance(node.func, ast.Name):
            if node.func.id == 'eval':
                is_eval = True
            elif node.func.id == 'exec':
                is_exec = True

        if (is_eval or is_exec) and node.args:
            first_arg = node.args[0]
            is_literal = isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str)
            severity = "high" if is_literal else "critical"
            name = "eval" if is_eval else "exec"
            
            lineno = node.lineno
            snippet = self.source_lines[lineno - 1] if 0 < lineno <= len(self.source_lines) else ""
            
            self.issues.append(Issue(
                title=f"Dangerous Use of '{name}'",
                description=(
                    f"Use of built-in function '{name}' is highly discouraged. "
                    "Evaluating dynamic code blocks can lead to arbitrary code execution vulnerabilities."
                ),
                severity=severity,
                category="security",
                line_number=lineno,
                code_snippet=snippet.strip(),
                suggestion=Suggestion(
                    original_code=snippet,
                    proposed_code="# Use alternative design or safe parsers like ast.literal_eval for data types.",
                    explanation=f"Avoid calling '{name}'. If you are parsing a Python literal, use 'ast.literal_eval()' instead, which is safe."
                )
            ))
        self.generic_visit(node)

def detect_code_injection(tree: ast.AST, source_lines: List[str]) -> List[Issue]:
    visitor = InjectionVisitor(source_lines)
    visitor.visit(tree)
    return visitor.issues
