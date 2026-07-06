import ast
from typing import List
from codereview.models import Issue, Suggestion

class SubprocessVisitor(ast.NodeVisitor):
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
        # 1. Check os.system, os.popen
        is_os_system = False
        is_os_popen = False
        func_name = ""

        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == 'os':
                if node.func.attr == 'system':
                    is_os_system = True
                    func_name = "os.system"
                elif node.func.attr == 'popen':
                    is_os_popen = True
                    func_name = "os.popen"
        elif isinstance(node.func, ast.Name):
            if node.func.id == 'system':
                is_os_system = True
                func_name = "system"
            elif node.func.id == 'popen':
                is_os_popen = True
                func_name = "popen"

        if (is_os_system or is_os_popen) and node.args:
            first_arg = node.args[0]
            is_dynamic = self._is_dynamic_string(first_arg) or (isinstance(first_arg, ast.Name) and first_arg.id in self.dynamic_vars)
            severity = "high" if is_dynamic else "medium"
            lineno = node.lineno
            snippet = self.source_lines[lineno - 1] if 0 < lineno <= len(self.source_lines) else ""
            
            self.issues.append(Issue(
                title="Unsafe Process Execution",
                description=(
                    f"Use of '{func_name}' is discouraged as it runs commands in a subshell, "
                    "introducing shell injection vulnerabilities if command strings are dynamic. "
                    "Use the 'subprocess' module instead, passing arguments as a list."
                ),
                severity=severity,
                category="security",
                line_number=lineno,
                code_snippet=snippet.strip(),
                suggestion=Suggestion(
                    original_code=snippet,
                    proposed_code="# Use subprocess.run with arguments list, e.g.:\n# subprocess.run([\"ls\", \"-l\"])",
                    explanation="Avoiding raw shell execution and utilizing subprocess with arguments list blocks command injection entirely."
                )
            ))

        # 2. Check subprocess calls with shell=True
        is_subprocess = False
        sub_func = ""
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == 'subprocess':
                if node.func.attr in ('run', 'Popen', 'call', 'check_call', 'check_output'):
                    is_subprocess = True
                    sub_func = f"subprocess.{node.func.attr}"
        elif isinstance(node.func, ast.Name):
            if node.func.id in ('run', 'Popen', 'call', 'check_call', 'check_output'):
                is_subprocess = True
                sub_func = node.func.id

        if is_subprocess:
            shell_true = False
            for kw in node.keywords:
                if kw.arg == 'shell':
                    if (isinstance(kw.value, ast.Constant) and kw.value.value is True) or \
                       (isinstance(kw.value, ast.Name) and kw.value.id == 'True'):
                        shell_true = True
                        break

            if shell_true and node.args:
                first_arg = node.args[0]
                is_dynamic = self._is_dynamic_string(first_arg) or (isinstance(first_arg, ast.Name) and first_arg.id in self.dynamic_vars)
                severity = "critical" if is_dynamic else "high"
                
                lineno = node.lineno
                snippet = self.source_lines[lineno - 1] if 0 < lineno <= len(self.source_lines) else ""
                
                self.issues.append(Issue(
                    title="Unsafe Subprocess with shell=True",
                    description=(
                        f"Calling '{sub_func}' with 'shell=True' runs the command through the shell. "
                        f"This bypasses argument escaping and is unsafe. "
                        "Avoid 'shell=True' and pass the command as a list of arguments."
                    ),
                    severity=severity,
                    category="security",
                    line_number=lineno,
                    code_snippet=snippet.strip(),
                    suggestion=Suggestion(
                        original_code=snippet,
                        proposed_code="# Avoid shell=True. E.g.:\n# subprocess.run([\"cmd\", \"arg1\", \"arg2\"])",
                        explanation="Passing command arguments as a list of strings instead of a single string executed by shell prevents malicious command insertion."
                    )
                ))

        self.generic_visit(node)

    def _is_dynamic_string(self, node) -> bool:
        if isinstance(node, ast.JoinedStr):
            return True
        if isinstance(node, ast.BinOp):
            if isinstance(node.op, ast.Add) and (self._is_string(node.left) or self._is_string(node.right)):
                return True
            if isinstance(node.op, ast.Mod) and self._is_string(node.left):
                return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'format':
            return True
        return False

    def _is_string(self, node) -> bool:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return True
        if isinstance(node, ast.JoinedStr):
            return True
        return False

def detect_subprocess_vulns(tree: ast.AST, source_lines: List[str]) -> List[Issue]:
    visitor = SubprocessVisitor(source_lines)
    visitor.visit(tree)
    return visitor.issues
