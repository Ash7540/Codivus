from codereview.models import RepositoryReviewResult
from codereview.reports.markdown import format_markdown_report as format_markdown_report  # noqa: F401
from codereview.reports.markdown import format_score


def format_console_report(result) -> str:
    lines = []
    is_repo = isinstance(result, RepositoryReviewResult)

    lines.append("=" * 60)
    lines.append("                  CODIVUS CODE REVIEW REPORT")
    lines.append("=" * 60)

    if is_repo:
        summary = result.summary
        score = result.overall_score
        lines.append("--- Repository Summary ---")
        lines.append(f"  Total Files Reviewed: {summary.total_files}")
        lines.append(f"  Total Lines of Code:  {summary.total_loc}")
        lines.append(f"  Total Issues Found:   {summary.total_issues}")
        lines.append(f"    - Critical: {summary.critical_issues}")
        lines.append(f"    - High:     {summary.high_issues}")
        lines.append(f"    - Medium:   {summary.medium_issues}")
        lines.append(f"    - Low:      {summary.low_issues}")
        lines.append("")
        lines.append("--- Quality Scores ---")
        lines.append(f"  Overall Score:     {format_score(score.overall_score)}")
        lines.append(f"  Security Score:    {format_score(score.security_score)}")
        lines.append(f"  Performance Score: {format_score(score.performance_score)}")
        lines.append(f"  Style/Bug Score:   {format_score(score.style_score)}")
        lines.append("")
        lines.append("--- Executive Summary ---")
        lines.append(summary.summary_text)
        lines.append("")
        if result.architecture_overview:
            lines.append("--- Architecture Overview ---")
            lines.append(result.architecture_overview)
            lines.append("")

        if result.repo_issues:
            lines.append("--- Repository-level Cross-file Issues ---")
            for idx, issue in enumerate(result.repo_issues, start=1):
                lines.append(
                    f"  {idx}. [{issue.category.upper()} - {issue.severity.upper()}] {issue.title}"
                )
                lines.append(f"     Description: {issue.description}")
                if issue.suggestion and issue.suggestion.proposed_code:
                    lines.append(
                        f"     Proposed Suggestion: {issue.suggestion.proposed_code}"
                    )
                lines.append("")

        lines.append("--- Individual File Issues ---")
        for filepath, f_res in result.file_reviews.items():
            if f_res.issues:
                lines.append(f"  File: {filepath} ({len(f_res.issues)} issues)")
                for issue in f_res.issues:
                    line_prefix = (
                        f"Line {issue.line_number}: " if issue.line_number else ""
                    )
                    lines.append(
                        f"    - [{issue.category.upper()} - {issue.severity.upper()}] {line_prefix}{issue.title}"
                    )
                    lines.append(f"      Description: {issue.description}")
                    if issue.code_snippet:
                        lines.append(f"      Code:        {issue.code_snippet}")
                    if issue.suggestion and issue.suggestion.proposed_code:
                        lines.append(
                            f"      Proposed:    {issue.suggestion.proposed_code}"
                        )
                lines.append("")
            else:
                lines.append(f"  File: {filepath} (No issues found)")
    else:
        summary = result.summary
        score = result.score
        lines.append("--- File Summary ---")
        lines.append(f"  Total Issues Found:   {summary.total_issues}")
        lines.append(f"    - Critical: {summary.critical_issues}")
        lines.append(f"    - High:     {summary.high_issues}")
        lines.append(f"    - Medium:   {summary.medium_issues}")
        lines.append(f"    - Low:      {summary.low_issues}")
        lines.append("")
        lines.append("--- Quality Scores ---")
        lines.append(f"  Overall Score:     {format_score(score.overall_score)}")
        lines.append(f"  Security Score:    {format_score(score.security_score)}")
        lines.append(f"  Performance Score: {format_score(score.performance_score)}")
        lines.append(f"  Style Score:       {format_score(score.style_score)}")
        lines.append("")
        lines.append("--- File Executive Summary ---")
        lines.append(summary.summary_text)
        lines.append("")

        if result.issues:
            lines.append("--- Detected Issues ---")
            for idx, issue in enumerate(result.issues, start=1):
                line_prefix = f"Line {issue.line_number}: " if issue.line_number else ""
                lines.append(
                    f"  {idx}. [{issue.category.upper()} - {issue.severity.upper()}] {line_prefix}{issue.title}"
                )
                lines.append(f"     Description: {issue.description}")
                if issue.code_snippet:
                    lines.append(f"     Code Snippet: {issue.code_snippet}")
                if issue.suggestion:
                    lines.append(f"     Suggestion:   {issue.suggestion.proposed_code}")
                    lines.append(f"     Explanation:  {issue.suggestion.explanation}")
                lines.append("")
        else:
            lines.append("  No issues found in this file.")

    lines.append("=" * 60)
    return "\n".join(lines)


def format_json_report(result) -> str:
    return result.model_dump_json(indent=2)
