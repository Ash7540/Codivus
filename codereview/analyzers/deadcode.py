import ast
from typing import List
from codereview.analyzers.base import BaseAnalyzer
from codereview.models import Issue, Suggestion, CodeContext


class AllNameRefCollector(ast.NodeVisitor):
    def __init__(self):
        self.loaded_names = set()

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.loaded_names.add(node.id)
        self.generic_visit(node)


class ImportCollector(ast.NodeVisitor):
    def __init__(self):
        self.imports = []  # items like {'bound_name': str, 'display_name': str, 'lineno': int}

    def visit_Import(self, node):
        for name_node in node.names:
            bound_name = name_node.asname or name_node.name.split(".")[0]
            self.imports.append(
                {
                    "bound_name": bound_name,
                    "display_name": name_node.name,
                    "lineno": node.lineno,
                }
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            for name_node in node.names:
                bound_name = name_node.asname or name_node.name
                self.imports.append(
                    {
                        "bound_name": bound_name,
                        "display_name": f"from {node.module} import {name_node.name}",
                        "lineno": node.lineno,
                    }
                )
        self.generic_visit(node)


class FunctionScopeVisitor(ast.NodeVisitor):
    def __init__(self):
        self.stored = {}  # name -> lineno
        self.loaded = set()
        self.params = set()

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            if not node.id.startswith("_") and node.id not in ("self", "cls"):
                self.stored[node.id] = node.lineno
        elif isinstance(node.ctx, ast.Load):
            self.loaded.add(node.id)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        # Skip nested functions to prevent mixing scopes
        pass

    def visit_AsyncFunctionDef(self, node):
        # Skip nested functions to prevent mixing scopes
        pass

    def visit_ClassDef(self, node):
        # Skip nested classes
        pass


class UnreachableCodeVisitor(ast.NodeVisitor):
    def __init__(self):
        self.unreachable_statements = []  # list of statement nodes

    def check_statements_list(self, body: list):
        terminal_found = False
        for stmt in body:
            # Skip empty nodes or docstrings
            if (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Constant)
                and isinstance(stmt.value.value, str)
            ):
                continue

            if terminal_found:
                self.unreachable_statements.append(stmt)
            elif isinstance(stmt, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                terminal_found = True

        # Traverse recursively
        for stmt in body:
            self.visit(stmt)

    def generic_visit(self, node):
        for field, value in ast.iter_fields(node):
            if isinstance(value, list) and field in ("body", "orelse", "finalbody"):
                self.check_statements_list(value)
            elif isinstance(value, ast.AST):
                self.visit(value)


class DeadCodeAnalyzer(BaseAnalyzer):
    def analyze(self, context: CodeContext) -> List[Issue]:
        issues = []
        try:
            tree = ast.parse(context.source_code)
        except Exception:
            return []

        lines = context.source_code.splitlines()

        # 1. Unused Imports
        import_collector = ImportCollector()
        import_collector.visit(tree)

        name_ref_collector = AllNameRefCollector()
        name_ref_collector.visit(tree)

        for imp in import_collector.imports:
            bound_name = imp["bound_name"]
            if bound_name not in name_ref_collector.loaded_names:
                lineno = imp["lineno"]
                snippet = lines[lineno - 1] if 0 < lineno <= len(lines) else ""
                issues.append(
                    Issue(
                        title="Unused Import",
                        description=f"Imported name '{bound_name}' is never used in this file.",
                        severity="low",
                        category="style",
                        line_number=lineno,
                        code_snippet=snippet.strip(),
                        suggestion=Suggestion(
                            original_code=snippet,
                            proposed_code=f"# Remove: {snippet.strip()}",
                            explanation="Removing unused imports keeps the codebase clean and speeds up initialization.",
                        ),
                    )
                )

        # 2. Unused Local Variables
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                scope_visitor = FunctionScopeVisitor()
                # Track parameters to ignore
                for arg in node.args.args:
                    scope_visitor.params.add(arg.arg)
                if hasattr(node.args, "posonlyargs") and node.args.posonlyargs:
                    for arg in node.args.posonlyargs:
                        scope_visitor.params.add(arg.arg)
                if hasattr(node.args, "kwonlyargs") and node.args.kwonlyargs:
                    for arg in node.args.kwonlyargs:
                        scope_visitor.params.add(arg.arg)
                if node.args.vararg:
                    scope_visitor.params.add(node.args.vararg.arg)
                if node.args.kwarg:
                    scope_visitor.params.add(node.args.kwarg.arg)

                for child in node.body:
                    scope_visitor.visit(child)

                unused_vars = (
                    scope_visitor.stored.keys()
                    - scope_visitor.loaded
                    - scope_visitor.params
                )
                for var in unused_vars:
                    lineno = scope_visitor.stored[var]
                    snippet = lines[lineno - 1] if 0 < lineno <= len(lines) else ""
                    issues.append(
                        Issue(
                            title="Unused Local Variable",
                            description=f"Local variable '{var}' is assigned in function '{node.name}' but never used.",
                            severity="low",
                            category="style",
                            line_number=lineno,
                            code_snippet=snippet.strip(),
                            suggestion=Suggestion(
                                original_code=snippet,
                                proposed_code=f"# Variable '{var}' can be removed or prefixed with '_'.",
                                explanation="Removing unused variables improves memory layout, readability, and limits confusion.",
                            ),
                        )
                    )

        # 3. Unreachable Code
        unreachable_visitor = UnreachableCodeVisitor()
        unreachable_visitor.visit(tree)
        for stmt in unreachable_visitor.unreachable_statements:
            lineno = stmt.lineno
            snippet = lines[lineno - 1] if 0 < lineno <= len(lines) else ""
            issues.append(
                Issue(
                    title="Unreachable Code",
                    description="This statement is unreachable because it follows a return, raise, break, or continue statement.",
                    severity="medium",
                    category="style",  # standard dead code is style/quality
                    line_number=lineno,
                    code_snippet=snippet.strip(),
                    suggestion=Suggestion(
                        original_code=snippet,
                        proposed_code=f"# Remove unreachable code: {snippet.strip()}",
                        explanation="Unreachable code can never run, adds noise, and should be cleaned up.",
                    ),
                )
            )

        return issues
