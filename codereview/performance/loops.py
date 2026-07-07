import ast
from typing import List
from codereview.models import Issue, Suggestion

class LoopPerformanceVisitor(ast.NodeVisitor):
    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.issues: List[Issue] = []
        self.in_loop = 0
        self.string_vars = set()

    def _is_string_expr(self, node) -> bool:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return True
        if isinstance(node, ast.JoinedStr):
            return True
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == 'str':
                return True
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'format':
                return True
        return False

    def visit_Assign(self, node):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id
            if self._is_string_expr(node.value):
                self.string_vars.add(var_name)
            else:
                self.string_vars.discard(var_name)
        self.generic_visit(node)

    def visit_For(self, node):
        self.in_loop += 1
        self.generic_visit(node)
        self.in_loop -= 1

    def visit_While(self, node):
        self.in_loop += 1
        self.generic_visit(node)
        self.in_loop -= 1

    def visit_AugAssign(self, node):
        if self.in_loop > 0:
            if isinstance(node.op, ast.Add) and isinstance(node.target, ast.Name):
                is_string = False
                if node.target.id in self.string_vars:
                    is_string = True
                elif self._is_string_expr(node.value):
                    is_string = True

                if is_string:
                    lineno = node.lineno
                    snippet = self.source_lines[lineno - 1] if 0 < lineno <= len(self.source_lines) else ""
                    self.issues.append(Issue(
                        title="String Concatenation in Loop",
                        description=(
                            f"String accumulation using '+=' on variable '{node.target.id}' detected inside a loop. "
                            "Strings in Python are immutable; concatenating them in a loop creates a new copy of the string "
                            "in each iteration, resulting in O(N^2) time complexity. "
                            "Instead, append strings to a list and use ''.join(list) after the loop."
                        ),
                        severity="medium",
                        category="performance",
                        line_number=lineno,
                        code_snippet=snippet.strip(),
                        suggestion=Suggestion(
                            original_code=snippet,
                            proposed_code=f"parts = []\nfor ...:\n    parts.append(...)\n{node.target.id} = ''.join(parts)",
                            explanation="Using list.append() followed by join() runs in O(N) linear time, avoiding redundant copy operations."
                        )
                    ))
        self.generic_visit(node)


    def visit_Call(self, node):
        if self.in_loop > 0:
            is_expensive = False
            call_type = ""
            proposed = ""
            
            # Check DB execute
            if isinstance(node.func, ast.Attribute) and node.func.attr in ('execute', 'executescript'):
                is_expensive = True
                call_type = f"Database query execution '{node.func.attr}'"
                proposed = "# Consider batching queries or using executescript/executemany to execute statements in bulk."
            
            # Check requests/httpx calls
            elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id in ('requests', 'httpx', 'urllib') and node.func.attr in ('get', 'post', 'put', 'delete', 'request', 'urlopen'):
                is_expensive = True
                call_type = f"HTTP request '{node.func.value.id}.{node.func.attr}'"
                proposed = "# Consider using connection pooling, session objects, or executing concurrent request calls outside the loop."
            
            # Check subprocess / process executions
            elif (isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == 'subprocess') or (isinstance(node.func, ast.Name) and node.func.id in ('system', 'popen', 'subprocess')):
                is_expensive = True
                call_type = "Process execution call"
                proposed = "# Avoid running external processes inside a loop. Execute parameters in bulk or design batch logic."

            if is_expensive:
                lineno = node.lineno
                snippet = self.source_lines[lineno - 1] if 0 < lineno <= len(self.source_lines) else ""
                self.issues.append(Issue(
                    title="Expensive Operation in Loop",
                    description=(
                        f"{call_type} detected inside a loop. "
                        "Performing I/O or subprocess creation inside a loop introduces substantial latency and overhead. "
                        "Refactor to perform operations outside the loop or utilize bulk APIs."
                    ),
                    severity="medium",
                    category="performance",
                    line_number=lineno,
                    code_snippet=snippet.strip(),
                    suggestion=Suggestion(
                        original_code=snippet,
                        proposed_code=proposed,
                        explanation="Performing network request, database call, or process creation inside a loop incurs significant roundtrip, connection, or process context-switching overhead."
                    ))
                )
        self.generic_visit(node)

def detect_loop_inefficiencies(tree: ast.AST, source_lines: List[str]) -> List[Issue]:
    visitor = LoopPerformanceVisitor(source_lines)
    visitor.visit(tree)
    return visitor.issues
