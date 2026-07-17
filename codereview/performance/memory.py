import ast
from typing import List
from codereview.models import Issue, Suggestion


class MemoryPerformanceVisitor(ast.NodeVisitor):
    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.issues: List[Issue] = []

    def visit_Call(self, node):
        # 1. Full file reads: .read() or .readlines()
        if isinstance(node.func, ast.Attribute) and node.func.attr in (
            "read",
            "readlines",
        ):
            is_unlimited = False
            if not node.args:
                is_unlimited = True

            if is_unlimited:
                lineno = node.lineno
                snippet = (
                    self.source_lines[lineno - 1]
                    if 0 < lineno <= len(self.source_lines)
                    else ""
                )
                method_name = node.func.attr
                self.issues.append(
                    Issue(
                        title="Memory-Inefficient File Read",
                        description=(
                            f"Calling '{method_name}()' without limit reads the entire file into memory at once. "
                            "For large files, this can cause significant memory pressure or Out Of Memory (OOM) errors. "
                            "Iterate over the file line-by-line ('for line in file:') or read in chunks."
                        ),
                        severity="medium",
                        category="performance",
                        line_number=lineno,
                        code_snippet=snippet.strip(),
                        suggestion=Suggestion(
                            original_code=snippet,
                            proposed_code="# Iterate line-by-line or read in chunks:\n# for line in file_obj:\n#     process(line)",
                            explanation="Iterating line-by-line or reading fixed-size chunks keeps memory usage constant at O(1) regardless of total file size.",
                        ),
                    )
                )

        # 2. List comprehension in aggregation functions
        is_agg = False
        agg_name = ""
        if isinstance(node.func, ast.Name) and node.func.id in (
            "sum",
            "any",
            "all",
            "min",
            "max",
            "tuple",
            "set",
        ):
            is_agg = True
            agg_name = node.func.id
        elif isinstance(node.func, ast.Attribute) and node.func.attr == "join":
            is_agg = True
            agg_name = "join"

        if is_agg and node.args:
            first_arg = node.args[0]
            if isinstance(first_arg, ast.ListComp):
                lineno = node.lineno
                snippet = (
                    self.source_lines[lineno - 1]
                    if 0 < lineno <= len(self.source_lines)
                    else ""
                )

                # Basic bracket removal for proposed code
                original_text = snippet.strip()
                proposed_text = original_text.replace("[", "").replace("]", "")

                self.issues.append(
                    Issue(
                        title="Unnecessary List Comprehension in Aggregation",
                        description=(
                            f"List comprehension passed to '{agg_name}()' allocates a full list in memory. "
                            f"Using a generator expression (by removing the square brackets) allows '{agg_name}()' "
                            "to consume items lazily, avoiding redundant memory allocation."
                        ),
                        severity="medium",
                        category="performance",
                        line_number=lineno,
                        code_snippet=original_text,
                        suggestion=Suggestion(
                            original_code=original_text,
                            proposed_code=proposed_text,
                            explanation="Generator expressions evaluate elements on-demand (lazily), saving space and avoiding the cost of building a full temporary list.",
                        ),
                    )
                )

        self.generic_visit(node)


def detect_memory_inefficiencies(tree: ast.AST, source_lines: List[str]) -> List[Issue]:
    visitor = MemoryPerformanceVisitor(source_lines)
    visitor.visit(tree)
    return visitor.issues
