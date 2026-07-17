import ast
from typing import List
from codereview.models import Issue, Suggestion


class SQLInjectionVisitor(ast.NodeVisitor):
    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.issues: List[Issue] = []
        # Map variable name -> lineno of dynamic assignment
        self.dynamic_vars = {}

    def visit_Assign(self, node):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id
            if self._is_dynamic_string(node.value):
                self.dynamic_vars[var_name] = node.lineno
            else:
                self.dynamic_vars.pop(var_name, None)
        self.generic_visit(node)

    def visit_Call(self, node):
        is_execute = False
        method_name = ""
        if isinstance(node.func, ast.Attribute) and node.func.attr in (
            "execute",
            "executemany",
            "executescript",
        ):
            is_execute = True
            method_name = node.func.attr
        elif isinstance(node.func, ast.Name) and node.func.id in (
            "execute",
            "executemany",
            "executescript",
        ):
            is_execute = True
            method_name = node.func.id

        if is_execute and node.args:
            first_arg = node.args[0]
            is_vuln = False
            reason = ""

            if self._is_dynamic_string(first_arg):
                is_vuln = True
                reason = "constructed directly using dynamic formatting (f-string, format(), concatenation, or % operator)"
            elif isinstance(first_arg, ast.Name) and first_arg.id in self.dynamic_vars:
                is_vuln = True
                reason = f"constructed dynamically at line {self.dynamic_vars[first_arg.id]} using formatting"

            if is_vuln:
                lineno = node.lineno
                snippet = (
                    self.source_lines[lineno - 1]
                    if 0 < lineno <= len(self.source_lines)
                    else ""
                )
                self.issues.append(
                    Issue(
                        title="Potential SQL Injection",
                        description=(
                            f"Database query execution '{method_name}' uses a query string {reason}. "
                            "This can lead to SQL injection vulnerabilities if user input is included in the string. "
                            "Use parameterized queries (e.g. passing parameters as a second argument) instead."
                        ),
                        severity="critical",
                        category="security",
                        line_number=lineno,
                        code_snippet=snippet.strip(),
                        suggestion=Suggestion(
                            original_code=snippet,
                            proposed_code='# Use parameterized queries, e.g.:\n# cursor.execute("SELECT * FROM users WHERE name = ?", (username,))',
                            explanation="Parameterized queries separate query structure from user input data, ensuring the input is never executed as SQL code.",
                        ),
                    )
                )
        self.generic_visit(node)

    def _is_dynamic_string(self, node) -> bool:
        if isinstance(node, ast.JoinedStr):
            return True
        if isinstance(node, ast.BinOp):
            if isinstance(node.op, ast.Add) and (
                self._is_string(node.left) or self._is_string(node.right)
            ):
                return True
            if isinstance(node.op, ast.Mod) and self._is_string(node.left):
                return True
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "format"
        ):
            return True
        return False

    def _is_string(self, node) -> bool:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return True
        if isinstance(node, ast.JoinedStr):
            return True
        return False


def detect_sql_injection(tree: ast.AST, source_lines: List[str]) -> List[Issue]:
    visitor = SQLInjectionVisitor(source_lines)
    visitor.visit(tree)
    return visitor.issues
