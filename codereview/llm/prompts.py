from typing import List, Optional
from codereview.models import CodeContext, Issue

SYSTEM_PROMPT = """
You are an expert software engineer and security auditor. Your task is to perform an automated code review on the provided file.
Analyze the code for:
1. Logic bugs and edge cases.
2. Security vulnerabilities (e.g. injection, hardcoded secrets, unsafe usage).
3. Performance bottlenecks and inefficiencies.
4. Naming convention, formatting, docstrings, and general style issues.

Provide a comprehensive, objective, and constructive review.
For every issue you identify, provide:
- A clear, descriptive title.
- A thorough explanation.
- The severity ('low', 'medium', 'high', 'critical').
- The category ('bug', 'style', 'performance', 'security').
- The line number and code snippet containing the issue.
- A proposed code correction (suggestion) with a clear explanation of why it helps.

Also, calculate quality scores (0 to 100) for overall, security, performance, and style.
Finally, compile a summary of findings.
"""

def format_review_prompt(context: CodeContext, static_issues: Optional[List[Issue]] = None) -> str:
    # Build structural outline
    imports_str = "\n".join([
        f"  - {imp.from_module + '.' if imp.from_module else ''}{imp.name}"
        for imp in context.imports
    ]) or "  - None"

    classes_str = ""
    for cls in context.classes:
        bases_str = f"({', '.join(cls.bases)})" if cls.bases else ""
        classes_str += f"  - Class `{cls.name}{bases_str}` (Lines {cls.start_line}-{cls.end_line})\n"
        for method in cls.methods:
            classes_str += f"    - Method `{method.name}({', '.join(method.args)})` (Lines {method.start_line}-{method.end_line})\n"
            
    classes_str = classes_str.strip() or "  - None"

    functions_str = "\n".join([
        f"  - Function `{func.name}({', '.join(func.args)})` (Lines {func.start_line}-{func.end_line})"
        for func in context.functions
    ]) or "  - None"

    stats_str = (
        f"  - Lines of Code (LOC): {context.stats.loc}\n"
        f"  - Comment Lines:       {context.stats.comment_lines}\n"
        f"  - Blank Lines:         {context.stats.blank_lines}\n"
        f"  - Classes Count:       {context.stats.num_classes}\n"
        f"  - Functions Count:     {context.stats.num_functions}"
    )

    static_findings_block = ""
    if static_issues:
        static_findings_block = "\n--- Detected Static Analysis Findings ---\n"
        for idx, issue in enumerate(static_issues, start=1):
            line_str = f"Line {issue.line_number}: " if issue.line_number else ""
            static_findings_block += f"  {idx}. [{issue.category.upper()} - {issue.severity.upper()}] {line_str}{issue.title}: {issue.description}\n"
        static_findings_block += "\nPlease review the code context and the above static findings. Suggest deep solutions and expand on other logic, performance, style, or security issues not covered by these static analysis tools. Avoid duplicating these exact findings unless adding significantly more depth.\n"

    return f"""
Please review the following file:
Filename: {context.filename}
File Path: {context.file_path}

--- Code Structure Outline ---
Imports:
{imports_str}

Classes:
{classes_str}

Module-Level Functions:
{functions_str}

File Statistics:
{stats_str}
{static_findings_block}
--- Source Code ---
```python
{context.source_code}
```
"""
