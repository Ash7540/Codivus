import json
from codereview.models import ReviewResult, RepositoryReviewResult

def format_score(score: float) -> str:
    if score >= 90.0:
        return f"{score:.1f}/100 (Excellent)"
    elif score >= 70.0:
        return f"{score:.1f}/100 (Good)"
    else:
        return f"{score:.1f}/100 (Action Required)"

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
                lines.append(f"  {idx}. [{issue.category.upper()} - {issue.severity.upper()}] {issue.title}")
                lines.append(f"     Description: {issue.description}")
                if issue.suggestion and issue.suggestion.proposed_code:
                    lines.append(f"     Proposed Suggestion: {issue.suggestion.proposed_code}")
                lines.append("")
                
        # Group file reviews
        lines.append("--- Individual File Issues ---")
        for filepath, f_res in result.file_reviews.items():
            if f_res.issues:
                lines.append(f"  File: {filepath} ({len(f_res.issues)} issues)")
                for issue in f_res.issues:
                    line_prefix = f"Line {issue.line_number}: " if issue.line_number else ""
                    lines.append(f"    - [{issue.category.upper()} - {issue.severity.upper()}] {line_prefix}{issue.title}")
                    lines.append(f"      Description: {issue.description}")
                    if issue.code_snippet:
                        lines.append(f"      Code:        {issue.code_snippet}")
                    if issue.suggestion and issue.suggestion.proposed_code:
                        lines.append(f"      Proposed:    {issue.suggestion.proposed_code}")
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
                lines.append(f"  {idx}. [{issue.category.upper()} - {issue.severity.upper()}] {line_prefix}{issue.title}")
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
        lines.append(f"- **Total Issues Found:** {summary.total_issues} (Critical: {summary.critical_issues}, High: {summary.high_issues}, Medium: {summary.medium_issues}, Low: {summary.low_issues})")
        lines.append("")
        lines.append("## Quality Scores")
        lines.append("| Category | Score | Status |")
        lines.append("| --- | --- | --- |")
        lines.append(f"| **Overall** | {score.overall_score:.1f}/100 | {format_score(score.overall_score).split()[-1]} |")
        lines.append(f"| Security | {score.security_score:.1f}/100 | {format_score(score.security_score).split()[-1]} |")
        lines.append(f"| Performance | {score.performance_score:.1f}/100 | {format_score(score.performance_score).split()[-1]} |")
        lines.append(f"| Style/Bug | {score.style_score:.1f}/100 | {format_score(score.style_score).split()[-1]} |")
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
                lines.append(f"### {idx}. [{issue.category.upper()} - {issue.severity.upper()}] {issue.title}")
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
                lines.append(f"<details><summary><b>{filepath}</b> ({len(f_res.issues)} issues)</summary>")
                lines.append("")
                for issue in f_res.issues:
                    line_str = f"Line {issue.line_number}: " if issue.line_number else ""
                    lines.append(f"#### [{issue.category.upper()} - {issue.severity.upper()}] {line_str}{issue.title}")
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
        lines.append(f"- **Total Issues Found:** {summary.total_issues} (Critical: {summary.critical_issues}, High: {summary.high_issues}, Medium: {summary.medium_issues}, Low: {summary.low_issues})")
        lines.append("")
        lines.append("## Quality Scores")
        lines.append("| Category | Score | Status |")
        lines.append("| --- | --- | --- |")
        lines.append(f"| **Overall** | {score.overall_score:.1f}/100 | {format_score(score.overall_score).split()[-1]} |")
        lines.append(f"| Security | {score.security_score:.1f}/100 | {format_score(score.security_score).split()[-1]} |")
        lines.append(f"| Performance | {score.performance_score:.1f}/100 | {format_score(score.performance_score).split()[-1]} |")
        lines.append(f"| Style | {score.style_score:.1f}/100 | {format_score(score.style_score).split()[-1]} |")
        lines.append("")
        lines.append("## File Executive Summary")
        lines.append(summary.summary_text)
        lines.append("")
        
        if result.issues:
            lines.append("## Detected Issues")
            for idx, issue in enumerate(result.issues, start=1):
                line_str = f"Line {issue.line_number}: " if issue.line_number else ""
                lines.append(f"### {idx}. [{issue.category.upper()} - {issue.severity.upper()}] {line_str}{issue.title}")
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

def format_json_report(result) -> str:
    return result.model_dump_json(indent=2)
