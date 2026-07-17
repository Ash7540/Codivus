import ast
from typing import List
from codereview.models import Issue, Suggestion


class AsyncPerformanceVisitor(ast.NodeVisitor):
    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.issues: List[Issue] = []
        self.in_async_func = False
        self.in_loop = 0

    def visit_AsyncFunctionDef(self, node):
        old_val = self.in_async_func
        self.in_async_func = True
        self.generic_visit(node)
        self.in_async_func = old_val

    def visit_For(self, node):
        self.in_loop += 1
        self.generic_visit(node)
        self.in_loop -= 1

    def visit_While(self, node):
        self.in_loop += 1
        self.generic_visit(node)
        self.in_loop -= 1

    def visit_Call(self, node):
        if self.in_async_func:
            is_blocking = False
            func_detail = ""
            proposed = ""

            # Check time.sleep
            if (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "time"
                and node.func.attr == "sleep"
            ):
                is_blocking = True
                func_detail = "time.sleep()"
                proposed = "await asyncio.sleep(...)"
            elif isinstance(node.func, ast.Name) and node.func.id == "sleep":
                is_blocking = True
                func_detail = "sleep()"
                proposed = "await asyncio.sleep(...)"

            # Check requests/urllib blocking
            elif (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in ("requests", "urllib")
                and node.func.attr
                in ("get", "post", "put", "delete", "request", "urlopen")
            ):
                is_blocking = True
                func_detail = (
                    f"blocking sync call '{node.func.value.id}.{node.func.attr}()'"
                )
                proposed = "await httpx.AsyncClient().get(...)"

            # Check subprocess call (blocking)
            elif (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "subprocess"
            ) or (
                isinstance(node.func, ast.Name)
                and node.func.id in ("system", "popen", "subprocess")
            ):
                is_blocking = True
                func_detail = "blocking subprocess call"
                proposed = "await asyncio.create_subprocess_exec(...)"

            if is_blocking:
                lineno = node.lineno
                snippet = (
                    self.source_lines[lineno - 1]
                    if 0 < lineno <= len(self.source_lines)
                    else ""
                )
                self.issues.append(
                    Issue(
                        title="Blocking Call in Async Function",
                        description=(
                            f"Use of blocking call '{func_detail}' inside an async function. "
                            "Blocking functions halt the entire event loop, preventing other async tasks from running. "
                            f"Use an asynchronous equivalent (e.g. '{proposed}') instead."
                        ),
                        severity="high",
                        category="performance",
                        line_number=lineno,
                        code_snippet=snippet.strip(),
                        suggestion=Suggestion(
                            original_code=snippet,
                            proposed_code=proposed,
                            explanation="Async functions should never block. Using non-blocking async calls allows the asyncio event loop to handle concurrent tasks efficiently.",
                        ),
                    )
                )

        self.generic_visit(node)

    def visit_Await(self, node):
        if self.in_loop > 0:
            lineno = node.lineno
            snippet = (
                self.source_lines[lineno - 1]
                if 0 < lineno <= len(self.source_lines)
                else ""
            )
            self.issues.append(
                Issue(
                    title="Sequential Await in Loop",
                    description=(
                        "An 'await' expression is executed inside a loop. "
                        "This forces each asynchronous operation to complete before starting the next one, "
                        "running them sequentially rather than concurrently. "
                        "Consider utilizing 'asyncio.gather()' to execute tasks in parallel."
                    ),
                    severity="medium",
                    category="performance",
                    line_number=lineno,
                    code_snippet=snippet.strip(),
                    suggestion=Suggestion(
                        original_code=snippet,
                        proposed_code="# Run tasks concurrently:\n# tasks = [my_func(x) for x in items]\n# results = await asyncio.gather(*tasks)",
                        explanation="Awaiting inside a loop is synchronous in nature. Executing concurrent awaits using gather() allows operations to overlap, speeding up processing.",
                    ),
                )
            )
        self.generic_visit(node)


def detect_async_misuse(tree: ast.AST, source_lines: List[str]) -> List[Issue]:
    visitor = AsyncPerformanceVisitor(source_lines)
    visitor.visit(tree)
    return visitor.issues
