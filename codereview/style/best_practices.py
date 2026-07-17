import ast
from typing import List
from codereview.models import Issue, Suggestion


class BestPracticesVisitor(ast.NodeVisitor):
    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.issues: List[Issue] = []

    def visit_FunctionDef(self, node):
        self._check_mutable_defaults(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self._check_mutable_defaults(node)
        self.generic_visit(node)

    def _check_mutable_defaults(self, node):
        defaults = node.args.defaults
        num_args = len(node.args.args)
        num_defaults = len(defaults)

        for i, default in enumerate(defaults):
            if self._is_mutable_node(default):
                param_index = num_args - num_defaults + i
                param_name = node.args.args[param_index].arg
                lineno = default.lineno
                snippet = (
                    self.source_lines[lineno - 1]
                    if 0 < lineno <= len(self.source_lines)
                    else ""
                )
                self.issues.append(
                    Issue(
                        title="Mutable Default Argument",
                        description=(
                            f"Parameter '{param_name}' in function '{node.name}' uses a mutable default argument. "
                            "Python default arguments are evaluated once at definition time, which means "
                            "the mutable default will be shared across all function calls."
                        ),
                        severity="medium",
                        category="style",
                        line_number=lineno,
                        code_snippet=snippet.strip(),
                        suggestion=Suggestion(
                            original_code=snippet,
                            proposed_code=f"def {node.name}({param_name}=None):\n    if {param_name} is None:\n        {param_name} = []",
                            explanation="Using None as a default value and initializing inside the function scope prevents sharing mutable state across calls.",
                        ),
                    )
                )

        for param, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
            if default and self._is_mutable_node(default):
                lineno = default.lineno
                snippet = (
                    self.source_lines[lineno - 1]
                    if 0 < lineno <= len(self.source_lines)
                    else ""
                )
                self.issues.append(
                    Issue(
                        title="Mutable Default Argument",
                        description=(
                            f"Keyword-only parameter '{param.arg}' in function '{node.name}' uses a mutable default argument. "
                            "Python default arguments are evaluated once at definition time."
                        ),
                        severity="medium",
                        category="style",
                        line_number=lineno,
                        code_snippet=snippet.strip(),
                        suggestion=Suggestion(
                            original_code=snippet,
                            proposed_code=f"def {node.name}(*, {param.arg}=None):\n    if {param.arg} is None:\n        {param.arg} = {{}}",
                            explanation="Using None as a default value prevents sharing mutable state across calls.",
                        ),
                    )
                )

    def _is_mutable_node(self, node) -> bool:
        if isinstance(node, (ast.List, ast.Dict, ast.Set)):
            return True
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in (
                "list",
                "dict",
                "set",
            ):
                return True
        return False

    def visit_ImportFrom(self, node):
        for alias in node.names:
            if alias.name == "*":
                lineno = node.lineno
                snippet = (
                    self.source_lines[lineno - 1]
                    if 0 < lineno <= len(self.source_lines)
                    else ""
                )
                self.issues.append(
                    Issue(
                        title="Wildcard Import Detected",
                        description=(
                            f"Wildcard import 'from {node.module} import *' detected. "
                            "Wildcard imports pollute the namespace, make static analysis difficult, "
                            "and can hide name conflict bugs."
                        ),
                        severity="medium",
                        category="style",
                        line_number=lineno,
                        code_snippet=snippet.strip(),
                        suggestion=Suggestion(
                            original_code=snippet,
                            proposed_code=f"# Explicitly import names instead:\n# from {node.module} import name1, name2",
                            explanation="Explicit imports clarify which names are used in the module and prevent name clashes.",
                        ),
                    )
                )
        self.generic_visit(node)

    def visit_Compare(self, node):
        if len(node.ops) == 1 and isinstance(node.ops[0], (ast.Is, ast.IsNot)):
            left = node.left
            right = node.comparators[0]

            is_literal = False
            for val in (left, right):
                if isinstance(val, ast.Constant):
                    if val.value not in (None, True, False):
                        is_literal = True
                        break

            if is_literal:
                lineno = node.lineno
                snippet = (
                    self.source_lines[lineno - 1]
                    if 0 < lineno <= len(self.source_lines)
                    else ""
                )
                op_str = "is" if isinstance(node.ops[0], ast.Is) else "is not"
                eq_str = "==" if isinstance(node.ops[0], ast.Is) else "!="
                self.issues.append(
                    Issue(
                        title="Literal Identity Comparison",
                        description=(
                            f"Identity comparison operator '{op_str}' used against a literal. "
                            "Identity comparisons check for object identity (same memory address), which may "
                            f"fail for literals depending on the compiler. Use equality '{eq_str}' instead."
                        ),
                        severity="medium",
                        category="style",
                        line_number=lineno,
                        code_snippet=snippet.strip(),
                        suggestion=Suggestion(
                            original_code=snippet,
                            proposed_code=f"value {eq_str} literal",
                            explanation="Equality comparisons compare values, which is the correct and safe way to match literals.",
                        ),
                    )
                )
        self.generic_visit(node)


def detect_best_practice_violations(
    tree: ast.AST, source_lines: List[str]
) -> List[Issue]:
    visitor = BestPracticesVisitor(source_lines)
    visitor.visit(tree)
    return visitor.issues
