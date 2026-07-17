import os
import sys
import json
from unittest.mock import patch, MagicMock
from codereview.cli.main import main
from codereview.cli.report import (
    format_console_report,
    format_markdown_report,
    format_json_report,
)
from codereview.models import (
    ReviewResult,
    Summary,
    Score,
    RepositoryReviewResult,
    RepositorySummary,
)


def test_report_formatters():
    # Setup dummy single file review result
    result = ReviewResult(
        summary=Summary(
            total_issues=1,
            critical_issues=0,
            high_issues=0,
            medium_issues=0,
            low_issues=1,
            summary_text="Mock single file review summary.",
        ),
        score=Score(
            overall_score=85.0,
            security_score=100.0,
            performance_score=90.0,
            style_score=65.0,
        ),
        issues=[],
        timestamp="2026-07-11T12:00:00Z",
    )

    console_out = format_console_report(result)
    assert "CODIVUS CODE REVIEW REPORT" in console_out
    assert "85.0/100" in console_out
    assert "Mock single file review summary." in console_out

    markdown_out = format_markdown_report(result)
    assert "# Codivus Code Review Report" in markdown_out
    assert "Mock single file review summary." in markdown_out

    json_out = format_json_report(result)
    assert '"overall_score": 85.0' in json_out


def test_repo_report_formatters():
    # Setup dummy repo review result
    result = RepositoryReviewResult(
        summary=RepositorySummary(
            total_files=2,
            total_loc=100,
            total_issues=1,
            critical_issues=0,
            high_issues=0,
            medium_issues=0,
            low_issues=1,
            summary_text="Mock repository review summary.",
        ),
        overall_score=Score(
            overall_score=90.0,
            security_score=95.0,
            performance_score=90.0,
            style_score=85.0,
        ),
        file_reviews={},
        repo_issues=[],
        architecture_overview="Mock repo architecture overview.",
        folder_structure="my_project/\n└── a.py",
        timestamp="2026-07-11T12:00:00Z",
    )

    console_out = format_console_report(result)
    assert "Total Files Reviewed: 2" in console_out
    assert "Mock repository review summary." in console_out
    assert "Mock repo architecture overview." in console_out

    markdown_out = format_markdown_report(result)
    assert "Mock repo architecture overview." in markdown_out
    assert "my_project/" in result.folder_structure


@patch("codereview.cli.review.Reviewer")
@patch("codereview.cli.review.os.path.isdir")
@patch("codereview.cli.review.os.path.exists")
def test_cli_execution_flows(mock_exists, mock_isdir, mock_reviewer_class, tmp_path):
    mock_exists.return_value = True
    mock_isdir.return_value = False

    # Mock reviewer instance and methods
    mock_reviewer = MagicMock()
    mock_reviewer_class.return_value = mock_reviewer

    # ReviewResult mock
    dummy_res = ReviewResult(
        summary=Summary(
            total_issues=0,
            critical_issues=0,
            high_issues=0,
            medium_issues=0,
            low_issues=0,
            summary_text="OK",
        ),
        score=Score(
            overall_score=100.0,
            security_score=100.0,
            performance_score=100.0,
            style_score=100.0,
        ),
        issues=[],
        timestamp="2026-07-11T12:00:00Z",
    )
    mock_reviewer.review_file.return_value = dummy_res
    mock_reviewer.review_staged.return_value = dummy_res
    mock_reviewer.review_commit.return_value = dummy_res

    # 1. Test review file
    test_args = ["codivus", "a.py"]
    with patch.object(sys, "argv", test_args):
        with patch("builtins.print") as mock_print:
            main()
            mock_reviewer.review_file.assert_called_once_with(os.path.abspath("a.py"))
            mock_print.assert_called()

    # Reset mock
    mock_reviewer.review_file.reset_mock()

    # 2. Test review staged
    test_args = ["codivus", "--staged"]
    with patch.object(sys, "argv", test_args):
        main()
        mock_reviewer.review_staged.assert_called_once_with(".")

    # 3. Test review commit
    test_args = ["codivus", "--commit", "hash123"]
    with patch.object(sys, "argv", test_args):
        main()
        mock_reviewer.review_commit.assert_called_once_with("hash123", ".")

    # 4. Test output redirect to file
    out_file = tmp_path / "report.json"
    test_args = ["codivus", "a.py", "--format", "json", "--output", str(out_file)]
    with patch.object(sys, "argv", test_args):
        main()
        assert out_file.exists()
        content = json.loads(out_file.read_text(encoding="utf-8"))
        assert content["score"]["overall_score"] == 100.0
