import ast
import re
from typing import List
from codereview.models import Issue, Suggestion

CLASS_NAME_RE = re.compile(r'^[A-Z][a-zA-Z0-9]*$')
FUNCTION_NAME_RE = re.compile(r'^[a-z_][a-z0-9_]*$')
MAGIC_METHOD_RE = re.compile(r'^__[a-z0-9_]+__$')
VARIABLE_NAME_RE = re.compile(r'^[a-z_][a-z0-9_]*$')

class NamingVisitor(ast.NodeVisitor):
    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.issues: List[Issue] = []
        self.in_function = False

    def visit_ClassDef(self, node):
        if not CLASS_NAME_RE.match(node.name):
            lineno = node.lineno
            snippet = self.source_lines[lineno - 1] if 0 < lineno <= len(self.source_lines) else ""
            self.issues.append(Issue(
                title="PEP 8 Naming Violation: Class Name",
                description=(
                    f"Class name '{node.name}' does not follow PEP 8 CamelCase naming convention. "
                    "Class names should start with an uppercase letter and use mixed case."
                ),
                severity="low",
                category="style",
                line_number=lineno,
                code_snippet=snippet.strip(),
                suggestion=Suggestion(
                    original_code=snippet,
                    proposed_code=f"# Use CamelCase, e.g.: class {node.name[0].upper() + node.name[1:]}:",
                    explanation="Following standard naming conventions improves consistency and readability for Python developers."
                )
            ))
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self._check_function_naming(node)
        
        old_val = self.in_function
        self.in_function = True
        self.generic_visit(node)
        self.in_function = old_val

    def visit_AsyncFunctionDef(self, node):
        self._check_function_naming(node)
        
        old_val = self.in_function
        self.in_function = True
        self.generic_visit(node)
        self.in_function = old_val

    def _check_function_naming(self, node):
        name = node.name
        if MAGIC_METHOD_RE.match(name):
            return
            
        if not FUNCTION_NAME_RE.match(name):
            lineno = node.lineno
            snippet = self.source_lines[lineno - 1] if 0 < lineno <= len(self.source_lines) else ""
            self.issues.append(Issue(
                title="PEP 8 Naming Violation: Function Name",
                description=(
                    f"Function/method name '{name}' does not follow PEP 8 snake_case naming convention. "
                    "Function and method names should be lowercase, with words separated by underscores."
                ),
                severity="low",
                category="style",
                line_number=lineno,
                code_snippet=snippet.strip(),
                suggestion=Suggestion(
                    original_code=snippet,
                    proposed_code=f"# Use snake_case, e.g.: def {name.lower()}(...):",
                    explanation="PEP 8 recommends snake_case for all functions and class methods."
                )
            ))

        for arg in node.args.args:
            self._check_variable_naming(arg.arg, "Parameter", arg.lineno)
        for arg in getattr(node.args, "posonlyargs", []):
            self._check_variable_naming(arg.arg, "Parameter", arg.lineno)
        for arg in getattr(node.args, "kwonlyargs", []):
            self._check_variable_naming(arg.arg, "Parameter", arg.lineno)
        if node.args.vararg:
            self._check_variable_naming(node.args.vararg.arg, "Parameter", node.args.vararg.lineno)
        if node.args.kwarg:
            self._check_variable_naming(node.args.kwarg.arg, "Parameter", node.args.kwarg.lineno)

    def visit_Assign(self, node):
        if self.in_function:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self._check_variable_naming(target.id, "Variable", target.lineno)
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        if self.in_function:
            if isinstance(node.target, ast.Name):
                self._check_variable_naming(node.target.id, "Variable", node.target.lineno)
        self.generic_visit(node)

    def _check_variable_naming(self, name: str, entity_type: str, lineno: int):
        if name in ("self", "cls", "_"):
            return
            
        if not VARIABLE_NAME_RE.match(name):
            snippet = self.source_lines[lineno - 1] if 0 < lineno <= len(self.source_lines) else ""
            self.issues.append(Issue(
                title=f"PEP 8 Naming Violation: {entity_type} Name",
                description=(
                    f"{entity_type} name '{name}' does not follow PEP 8 snake_case naming convention. "
                    f"{entity_type} names should be lowercase, with words separated by underscores."
                ),
                severity="low",
                category="style",
                line_number=lineno,
                code_snippet=snippet.strip(),
                suggestion=Suggestion(
                    original_code=snippet,
                    proposed_code=f"# Use snake_case, e.g.: {name.lower()} = ...",
                    explanation="PEP 8 recommends snake_case for local variables and parameters inside methods/functions."
                )
            ))

def detect_naming_violations(tree: ast.AST, source_lines: List[str]) -> List[Issue]:
    visitor = NamingVisitor(source_lines)
    visitor.visit(tree)
    return visitor.issues
