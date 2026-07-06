import ast
from typing import List
from codereview.models import Issue, Suggestion

class XSSVisitor(ast.NodeVisitor):
    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.issues: List[Issue] = []

    def visit_Call(self, node):
        is_jinja_env = False
        if isinstance(node.func, ast.Name) and node.func.id == 'Environment':
            is_jinja_env = True
        elif isinstance(node.func, ast.Attribute) and node.func.attr == 'Environment':
            is_jinja_env = True

        if is_jinja_env:
            for kw in node.keywords:
                if kw.arg == 'autoescape':
                    if (isinstance(kw.value, ast.Constant) and kw.value.value is False) or \
                       (isinstance(kw.value, ast.Name) and kw.value.id == 'False'):
                        lineno = node.lineno
                        snippet = self.source_lines[lineno - 1] if 0 < lineno <= len(self.source_lines) else ""
                        self.issues.append(Issue(
                            title="Jinja2 Autoescape Disabled",
                            description=(
                                "Jinja2 Environment initialized with 'autoescape=False'. "
                                "This disables automatic HTML escaping and exposes the application to Cross-Site Scripting (XSS) vulnerabilities."
                            ),
                            severity="high",
                            category="security",
                            line_number=lineno,
                            code_snippet=snippet.strip(),
                            suggestion=Suggestion(
                                original_code=snippet,
                                proposed_code="Environment(autoescape=True)",
                                explanation="Autoescaping ensures that HTML characters like < and > are encoded, neutralizing potential XSS scripts."
                            )
                        ))
        self.generic_visit(node)

def detect_xss_vulns(tree: ast.AST, source_lines: List[str]) -> List[Issue]:
    visitor = XSSVisitor(source_lines)
    visitor.visit(tree)
    return visitor.issues
