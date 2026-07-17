import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from codereview.cli.main import main
from codereview.models import (
    ReviewResult,
    RepositoryReviewResult,
    Summary,
    Score,
    RepositorySummary,
)


@pytest.fixture(autouse=True)
def mock_load_dotenv():
    with patch("codereview.config.load_dotenv") as mock:
        yield mock


@pytest.fixture
def dummy_result():
    return ReviewResult(
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
        timestamp="2026-07-13T12:00:00Z",
    )


@pytest.fixture
def dummy_repo_result():
    return RepositoryReviewResult(
        summary=RepositorySummary(
            total_files=1,
            total_loc=10,
            total_issues=0,
            critical_issues=0,
            high_issues=0,
            medium_issues=0,
            low_issues=0,
            summary_text="OK",
        ),
        overall_score=Score(
            overall_score=100.0,
            security_score=100.0,
            performance_score=100.0,
            style_score=100.0,
        ),
        file_reviews={},
        repo_issues=[],
        architecture_overview="Overview",
        folder_structure="Folder",
        timestamp="2026-07-13T12:00:00Z",
    )


@patch("codereview.cli.review.Reviewer")
@patch("codereview.cli.review.os.path.exists")
@patch("codereview.cli.review.os.path.isdir")
def test_review_subcommand(mock_isdir, mock_exists, mock_reviewer_class, dummy_result):
    mock_exists.return_value = True
    mock_isdir.return_value = False

    mock_reviewer = MagicMock()
    mock_reviewer_class.return_value = mock_reviewer
    mock_reviewer.review_file.return_value = dummy_result

    test_args = ["codivus", "review", "a.py"]
    with patch.object(sys, "argv", test_args):
        main()
        mock_reviewer.review_file.assert_called_once_with(os.path.abspath("a.py"))


@patch("codereview.cli.repo.Reviewer")
@patch("codereview.cli.repo.os.path.exists")
@patch("codereview.cli.repo.os.path.isdir")
def test_repo_subcommand(
    mock_isdir, mock_exists, mock_reviewer_class, dummy_repo_result
):
    mock_exists.return_value = True
    mock_isdir.return_value = True

    mock_reviewer = MagicMock()
    mock_reviewer_class.return_value = mock_reviewer
    mock_reviewer.review_dir.return_value = dummy_repo_result

    test_args = ["codivus", "repo", "my_repo"]
    with patch.object(sys, "argv", test_args):
        main()
        mock_reviewer.review_dir.assert_called_once_with(os.path.abspath("my_repo"))


@patch("codereview.cli.repo.Reviewer")
@patch("codereview.cli.repo.os.path.exists")
def test_security_subcommand(mock_exists, mock_reviewer_class, dummy_result):
    mock_exists.return_value = True

    mock_reviewer = MagicMock()
    mock_reviewer_class.return_value = mock_reviewer
    mock_reviewer.review_file.return_value = dummy_result

    test_args = ["codivus", "security", "a.py"]
    with patch.object(sys, "argv", test_args):
        main()
        mock_reviewer.review_file.assert_called_once_with(
            os.path.abspath("a.py"), category_focus="security"
        )


@patch("codereview.cli.diff.Reviewer")
def test_diff_subcommand(mock_reviewer_class, dummy_repo_result):
    mock_reviewer = MagicMock()
    mock_reviewer_class.return_value = mock_reviewer
    mock_reviewer.review_diff.return_value = dummy_repo_result

    test_args = ["codivus", "diff", "main...feature", "my_repo"]
    with patch.object(sys, "argv", test_args):
        main()
        mock_reviewer.review_diff.assert_called_once_with("main...feature", "my_repo")


def test_config_subcommand(tmp_path):
    tmp_path / ".env"

    # 1. Test init
    with patch("codereview.cli.explain.os.path.exists", return_value=False):
        with patch("builtins.open", mock_open := MagicMock()):
            test_args = ["codivus", "config", "init"]
            with patch.object(sys, "argv", test_args):
                main()
                mock_open.assert_called_once()

    # 2. Test show
    mock_config = MagicMock()
    mock_config.default_provider = "openai"
    mock_config.default_model = "gpt-4o"
    mock_config.temperature = 0.2
    mock_config.openai_api_key = "sk-123456789012"

    with patch("builtins.print") as mock_print:
        test_args = ["codivus", "config", "show"]
        with patch.object(sys, "argv", test_args):
            from codereview.cli.explain import handle_config

            handle_config(MagicMock(config_subcommand="show"), mock_config)
            mock_print.assert_any_call("  DEFAULT_MODEL:    gpt-4o")
            mock_print.assert_any_call("  OPENAI_API_KEY:   sk-12345...9012")


@patch("codereview.cli.review.output_result")
@patch("codereview.cli.review.os.path.exists")
def test_report_subcommand(mock_exists, mock_output_result, dummy_result, tmp_path):
    mock_exists.return_value = True

    # Setup dummy JSON report file
    report_file = tmp_path / "report.json"
    report_file.write_text(dummy_result.model_dump_json(), encoding="utf-8")

    test_args = [
        "codivus",
        "report",
        str(report_file),
        "--format",
        "html",
        "--output",
        "out.html",
    ]
    with patch.object(sys, "argv", test_args):
        main()
        mock_output_result.assert_called_once()
