from codereview.models import RepositoryReviewResult


def format_score(score: float) -> str:
    if score >= 90.0:
        return f"{score:.1f}/100 (Excellent)"
    elif score >= 70.0:
        return f"{score:.1f}/100 (Good)"
    else:
        return f"{score:.1f}/100 (Action Required)"


def format_markdown_report(result) -> str:
    lines = []
    is_repo = isinstance(result, RepositoryReviewResult)

    lines.append("# Codivus Code Review Report")
    lines.append("")

    if is_repo:
        summary = result.summary
        score = result.overall_score
        lines.append("## Repository Summary")
        lines.append(f"- **Total Files Reviewed:** {summary.total_files}")
        lines.append(f"- **Total Lines of Code:** {summary.total_loc}")
        lines.append(
            f"- **Total Issues Found:** {summary.total_issues} (Critical: {summary.critical_issues}, High: {summary.high_issues}, Medium: {summary.medium_issues}, Low: {summary.low_issues})"
        )
        lines.append("")
        lines.append("## Quality Scores")
        lines.append("| Category | Score | Status |")
        lines.append("| --- | --- | --- |")
        lines.append(
            f"| **Overall** | {score.overall_score:.1f}/100 | {format_score(score.overall_score).split()[-1]} |"
        )
        lines.append(
            f"| Security | {score.security_score:.1f}/100 | {format_score(score.security_score).split()[-1]} |"
        )
        lines.append(
            f"| Performance | {score.performance_score:.1f}/100 | {format_score(score.performance_score).split()[-1]} |"
        )
        lines.append(
            f"| Style/Bug | {score.style_score:.1f}/100 | {format_score(score.style_score).split()[-1]} |"
        )
        lines.append("")
        lines.append("## Executive Summary")
        lines.append(summary.summary_text)
        lines.append("")
        if result.architecture_overview:
            lines.append("## Architecture Overview")
            lines.append(result.architecture_overview)
            lines.append("")

        if result.repo_issues:
            lines.append("## Repository-level Cross-file Issues")
            for idx, issue in enumerate(result.repo_issues, start=1):
                lines.append(
                    f"### {idx}. [{issue.category.upper()} - {issue.severity.upper()}] {issue.title}"
                )
                lines.append(f"{issue.description}")
                lines.append("")
                if issue.suggestion and issue.suggestion.proposed_code:
                    lines.append("```python")
                    lines.append(issue.suggestion.proposed_code)
                    lines.append("```")
                    lines.append("")

        lines.append("## File Issues Details")
        for filepath, f_res in result.file_reviews.items():
            if f_res.issues:
                lines.append(
                    f"<details><summary><b>{filepath}</b> ({len(f_res.issues)} issues)</summary>"
                )
                lines.append("")
                for issue in f_res.issues:
                    line_str = (
                        f"Line {issue.line_number}: " if issue.line_number else ""
                    )
                    lines.append(
                        f"#### [{issue.category.upper()} - {issue.severity.upper()}] {line_str}{issue.title}"
                    )
                    lines.append(f"{issue.description}")
                    lines.append("")
                    if issue.code_snippet:
                        lines.append("**Original Code:**")
                        lines.append("```python")
                        lines.append(issue.code_snippet)
                        lines.append("```")
                    if issue.suggestion:
                        lines.append("**Proposed Suggestion:**")
                        lines.append("```python")
                        lines.append(issue.suggestion.proposed_code)
                        lines.append("```")
                        lines.append(f"*{issue.suggestion.explanation}*")
                    lines.append("")
                lines.append("</details>")
                lines.append("")
            else:
                lines.append(f"- **{filepath}:** No issues found")
    else:
        summary = result.summary
        score = result.score
        lines.append("## File Summary")
        lines.append(
            f"- **Total Issues Found:** {summary.total_issues} (Critical: {summary.critical_issues}, High: {summary.high_issues}, Medium: {summary.medium_issues}, Low: {summary.low_issues})"
        )
        lines.append("")
        lines.append("## Quality Scores")
        lines.append("| Category | Score | Status |")
        lines.append("| --- | --- | --- |")
        lines.append(
            f"| **Overall** | {score.overall_score:.1f}/100 | {format_score(score.overall_score).split()[-1]} |"
        )
        lines.append(
            f"| Security | {score.security_score:.1f}/100 | {format_score(score.security_score).split()[-1]} |"
        )
        lines.append(
            f"| Performance | {score.performance_score:.1f}/100 | {format_score(score.performance_score).split()[-1]} |"
        )
        lines.append(
            f"| Style | {score.style_score:.1f}/100 | {format_score(score.style_score).split()[-1]} |"
        )
        lines.append("")
        lines.append("## File Executive Summary")
        lines.append(summary.summary_text)
        lines.append("")

        if result.issues:
            lines.append("## Detected Issues")
            for idx, issue in enumerate(result.issues, start=1):
                line_str = f"Line {issue.line_number}: " if issue.line_number else ""
                lines.append(
                    f"### {idx}. [{issue.category.upper()} - {issue.severity.upper()}] {line_str}{issue.title}"
                )
                lines.append(f"{issue.description}")
                lines.append("")
                if issue.code_snippet:
                    lines.append("**Original Code:**")
                    lines.append("```python")
                    lines.append(issue.code_snippet)
                    lines.append("```")
                if issue.suggestion:
                    lines.append("**Proposed Suggestion:**")
                    lines.append("```python")
                    lines.append(issue.suggestion.proposed_code)
                    lines.append("```")
                    lines.append(f"*{issue.suggestion.explanation}*")
                lines.append("")
        else:
            lines.append("No issues found in this file.")

    return "\n".join(lines)


def export_markdown(result, filepath: str) -> None:
    """
    Exports the review result to a Markdown file.
    """
    content = format_markdown_report(result)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
