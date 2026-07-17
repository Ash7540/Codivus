import ast
from typing import List
from codereview.models import Issue, Suggestion


class OptimisationVisitor(ast.NodeVisitor):
    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.issues: List[Issue] = []
        self.list_vars = {}  # name -> lineno

    def visit_Assign(self, node):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id
            is_list = False
            if isinstance(node.value, ast.List):
                is_list = True
            elif (
                isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "list"
            ):
                is_list = True

            if is_list:
                self.list_vars[var_name] = node.lineno
            else:
                self.list_vars.pop(var_name, None)
        self.generic_visit(node)

    def visit_Compare(self, node):
        if len(node.ops) == 1 and isinstance(node.ops[0], (ast.In, ast.NotIn)):
            right = node.comparators[0]
            if isinstance(right, ast.Name) and right.id in self.list_vars:
                lineno = node.lineno
                snippet = (
                    self.source_lines[lineno - 1]
                    if 0 < lineno <= len(self.source_lines)
                    else ""
                )
                self.issues.append(
                    Issue(
                        title="Membership Check on List",
                        description=(
                            f"Membership test ('in' or 'not in') against list '{right.id}' detected. "
                            "Searching in a list takes O(N) linear time. If the collection contains many items or is checked "
                            "frequently, consider converting it to a 'set' (which offers O(1) constant time lookups)."
                        ),
                        severity="low",
                        category="performance",
                        line_number=lineno,
                        code_snippet=snippet.strip(),
                        suggestion=Suggestion(
                            original_code=snippet,
                            proposed_code=f"# Convert to set for O(1) lookups, e.g.:\n# {right.id}_set = set({right.id})\n# if ... in {right.id}_set:",
                            explanation="Searching a list requires scanning elements sequentially. Converting to a set uses hashing for near-instant lookups.",
                        ),
                    )
                )
        self.generic_visit(node)


def detect_redundant_operations(tree: ast.AST, source_lines: List[str]) -> List[Issue]:
    visitor = OptimisationVisitor(source_lines)
    visitor.visit(tree)
    return visitor.issues
