import ast
from typing import List
from codereview.models import Issue, Suggestion


class CommentsVisitor(ast.NodeVisitor):
    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.issues: List[Issue] = []

    def visit_Module(self, node):
        if not ast.get_docstring(node):
            self.issues.append(
                Issue(
                    title="Missing Module Docstring",
                    description="This Python module is missing a module-level docstring at the beginning of the file.",
                    severity="low",
                    category="style",
                    line_number=1,
                    code_snippet="",
                    suggestion=Suggestion(
                        original_code="",
                        proposed_code='"""\nModule description goes here.\n"""',
                        explanation="PEP 257 recommends that all modules, classes, and public functions have docstrings explaining their purpose.",
                    ),
                )
            )
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        if not node.name.startswith("_"):
            if not ast.get_docstring(node):
                lineno = node.lineno
                snippet = (
                    self.source_lines[lineno - 1]
                    if 0 < lineno <= len(self.source_lines)
                    else ""
                )
                self.issues.append(
                    Issue(
                        title="Missing Class Docstring",
                        description=f"Public class '{node.name}' is missing a docstring explaining its design and usage.",
                        severity="low",
                        category="style",
                        line_number=lineno,
                        code_snippet=snippet.strip(),
                        suggestion=Suggestion(
                            original_code=snippet,
                            proposed_code=f'class {node.name}:\n    """Docstring explaining class goes here."""',
                            explanation="Class docstrings should explain class behavior, key methods, and attributes.",
                        ),
                    )
                )
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self._check_function_docstring(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self._check_function_docstring(node)
        self.generic_visit(node)

    def _check_function_docstring(self, node):
        name = node.name
        # Skip private functions and magic methods
        if name.startswith("_") or (name.startswith("__") and name.endswith("__")):
            return

        if not ast.get_docstring(node):
            lineno = node.lineno
            snippet = (
                self.source_lines[lineno - 1]
                if 0 < lineno <= len(self.source_lines)
                else ""
            )
            self.issues.append(
                Issue(
                    title="Missing Function Docstring",
                    description=f"Public function/method '{name}' is missing a docstring describing its behavior.",
                    severity="low",
                    category="style",
                    line_number=lineno,
                    code_snippet=snippet.strip(),
                    suggestion=Suggestion(
                        original_code=snippet,
                        proposed_code=f'def {name}(...):\n    """Docstring explaining function goes here."""',
                        explanation="PEP 257 states that all public functions and methods must have docstrings.",
                    ),
                )
            )


def detect_missing_comments(tree: ast.AST, source_lines: List[str]) -> List[Issue]:
    visitor = CommentsVisitor(source_lines)
    visitor.visit(tree)
    return visitor.issues
