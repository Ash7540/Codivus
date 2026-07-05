import os
from typing import Optional
from codereview.config import Config
from codereview.llm.router import get_provider
from codereview.models import ReviewResult, Summary, Score
from codereview.parsers import get_parser_for_file
from codereview.analyzers import run_static_analysis

class Reviewer:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.provider = get_provider(self.config.default_provider, self.config)

    def review_file(self, filepath: str) -> ReviewResult:
        """
        Reviews a single file and returns structured review results.
        """
        # Ensure filepath is absolute
        abs_filepath = os.path.abspath(filepath)
        
        if not os.path.exists(abs_filepath):
            raise FileNotFoundError(f"File not found: {abs_filepath}")
        
        if not os.path.isfile(abs_filepath):
            raise ValueError(f"Path is not a file: {abs_filepath}")
            
        try:
            with open(abs_filepath, "r", encoding="utf-8") as f:
                code_content = f.read()
        except Exception as e:
            raise RuntimeError(f"Failed to read file {abs_filepath}: {str(e)}")

        # 1. Parse file content into CodeContext
        parser = get_parser_for_file(abs_filepath)
        code_context = parser.parse_code(code_content, abs_filepath)

        # 2. Run deterministic static analysis
        static_issues = run_static_analysis(code_context)

        # 3. Invoke LLM provider with CodeContext and static analysis findings
        llm_result = self.provider.generate_review(code_context, static_issues)

        # 4. Merge static analysis issues with LLM issues
        combined_issues = static_issues + llm_result.issues

        # 5. Recalculate summary metrics based on the combined list
        total_issues = len(combined_issues)
        critical_count = sum(1 for i in combined_issues if i.severity.lower() == "critical")
        high_count = sum(1 for i in combined_issues if i.severity.lower() == "high")
        medium_count = sum(1 for i in combined_issues if i.severity.lower() == "medium")
        low_count = sum(1 for i in combined_issues if i.severity.lower() == "low")

        summary_text = llm_result.summary.summary_text
        if static_issues:
            summary_text += f" Static analysis discovered {len(static_issues)} additional issues."

        new_summary = Summary(
            total_issues=total_issues,
            critical_issues=critical_count,
            high_issues=high_count,
            medium_issues=medium_count,
            low_issues=low_count,
            summary_text=summary_text
        )

        # 6. Recalculate quality scores with static analysis deductions
        new_score = self._recalculate_scores(llm_result.score, static_issues)

        # 7. Construct final ReviewResult
        return ReviewResult(
            summary=new_summary,
            score=new_score,
            issues=combined_issues,
            timestamp=llm_result.timestamp
        )

    def _recalculate_scores(self, llm_score: Score, static_issues) -> Score:
        overall = llm_score.overall_score
        security = llm_score.security_score
        performance = llm_score.performance_score
        style = llm_score.style_score

        severity_deductions = {
            "critical": 20.0,
            "high": 15.0,
            "medium": 10.0,
            "low": 5.0
        }

        for issue in static_issues:
            deduction = severity_deductions.get(issue.severity.lower(), 5.0)
            overall -= deduction
            
            cat = issue.category.lower()
            if cat == "security":
                security -= deduction
            elif cat == "performance":
                performance -= deduction
            elif cat == "style" or cat == "bug":
                style -= deduction

        return Score(
            overall_score=max(0.0, min(100.0, overall)),
            security_score=max(0.0, min(100.0, security)),
            performance_score=max(0.0, min(100.0, performance)),
            style_score=max(0.0, min(100.0, style))
        )
