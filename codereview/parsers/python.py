import ast
import os
from codereview.parsers.base import BaseParser
from codereview.models.structure import (
    CodeContext,
    ImportInfo,
    FunctionInfo,
    ClassInfo,
    FileStats,
)


class PythonParser(BaseParser):
    def parse_code(self, code_content: str, file_path: str) -> CodeContext:
        try:
            tree = ast.parse(code_content)
        except SyntaxError as e:
            # Handle syntax errors gracefully by creating a minimal context
            filename = os.path.basename(file_path)
            stats = self._calculate_basic_stats(code_content, 0, 0)
            return CodeContext(
                file_path=file_path,
                filename=filename,
                functions=[],
                classes=[],
                imports=[],
                docstring=f"Syntax Error while parsing: {str(e)}",
                stats=stats,
                source_code=code_content,
            )

        filename = os.path.basename(file_path)
        module_docstring = ast.get_docstring(tree)

        # 1. Extract imports (walk tree to catch nested imports too)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name_node in node.names:
                    imports.append(
                        ImportInfo(
                            name=name_node.name,
                            alias=name_node.asname,
                            from_module=None,
                            line_number=node.lineno,
                        )
                    )
            elif isinstance(node, ast.ImportFrom):
                for name_node in node.names:
                    imports.append(
                        ImportInfo(
                            name=name_node.name,
                            alias=name_node.asname,
                            from_module=node.module,
                            line_number=node.lineno,
                        )
                    )

        # 2. Extract classes and functions (walk body for structural top-level declarations)
        functions = []
        classes = []

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(self._extract_function_info(node))
            elif isinstance(node, ast.ClassDef):
                classes.append(self._extract_class_info(node))

        # 3. Calculate statistics
        num_funcs = len(functions) + sum(len(c.methods) for c in classes)
        num_classes = len(classes)
        stats = self._calculate_basic_stats(code_content, num_funcs, num_classes)

        return CodeContext(
            file_path=file_path,
            filename=filename,
            functions=functions,
            classes=classes,
            imports=imports,
            docstring=module_docstring,
            stats=stats,
            source_code=code_content,
        )

    def _extract_function_info(self, node: ast.AST) -> FunctionInfo:
        # Extract arguments
        args = []
        if hasattr(node.args, "posonlyargs") and node.args.posonlyargs:
            args.extend([a.arg for a in node.args.posonlyargs])
        args.extend([a.arg for a in node.args.args])
        if node.args.vararg:
            args.append(f"*{node.args.vararg.arg}")
        if node.args.kwonlyargs:
            args.extend([a.arg for a in node.args.kwonlyargs])
        if node.args.kwarg:
            args.append(f"**{node.args.kwarg.arg}")

        start_line = node.lineno
        end_line = getattr(node, "end_lineno", node.lineno)

        return FunctionInfo(
            name=node.name,
            docstring=ast.get_docstring(node),
            start_line=start_line,
            end_line=end_line,
            args=args,
            complexity=1,  # placeholder
        )

    def _extract_class_info(self, node: ast.ClassDef) -> ClassInfo:
        bases = []
        for base in node.bases:
            try:
                bases.append(ast.unparse(base))
            except AttributeError:
                # Fallback for Python versions < 3.9
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(f"{base.attr}")
                else:
                    bases.append("")

        start_line = node.lineno
        end_line = getattr(node, "end_lineno", node.lineno)

        # Extract class methods
        methods = []
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(self._extract_function_info(child))

        return ClassInfo(
            name=node.name,
            docstring=ast.get_docstring(node),
            start_line=start_line,
            end_line=end_line,
            methods=methods,
            bases=bases,
        )

    def _calculate_basic_stats(
        self, code_content: str, num_functions: int, num_classes: int
    ) -> FileStats:
        lines = code_content.splitlines()
        total_lines = len(lines)
        blank_lines = 0
        comment_lines = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank_lines += 1
            elif stripped.startswith("#"):
                comment_lines += 1

        loc = total_lines - blank_lines - comment_lines

        return FileStats(
            loc=max(0, loc),
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            num_functions=num_functions,
            num_classes=num_classes,
        )
