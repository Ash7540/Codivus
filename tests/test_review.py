import pytest
from unittest.mock import MagicMock, patch
from codereview.config import Config
from codereview.reviewer import Reviewer
from codereview.models import ReviewResult, Summary, Score, Issue, Suggestion


def test_models_structure():
    # Verify we can instantiate all Pydantic models with dummy data
    suggestion = Suggestion(
        original_code="x = 1", proposed_code="x: int = 1", explanation="Add type hint"
    )
    issue = Issue(
        title="Missing type hint",
        description="Type hint should be present.",
        severity="low",
        category="style",
        line_number=1,
        code_snippet="x = 1",
        suggestion=suggestion,
    )
    score = Score(
        overall_score=90.0,
        security_score=100.0,
        performance_score=100.0,
        style_score=70.0,
    )
    summary = Summary(
        total_issues=1,
        critical_issues=0,
        high_issues=0,
        medium_issues=0,
        low_issues=1,
        summary_text="One styling issue found.",
    )
    review_result = ReviewResult(
        summary=summary, score=score, issues=[issue], timestamp="2026-07-03T12:00:00Z"
    )

    assert review_result.summary.total_issues == 1
    assert review_result.score.overall_score == 90.0
    assert len(review_result.issues) == 1
    assert review_result.issues[0].suggestion.original_code == "x = 1"


@patch("codereview.config.load_dotenv")
@patch("os.getenv")
def test_config_defaults(mock_getenv, mock_load_dotenv):
    # Setup getenv mock to respect standard default fallback argument
    mock_getenv.side_effect = lambda key, default=None: default

    config = Config()
    assert config.default_provider == "openai"
    assert config.default_model == "gpt-4o-mini"
    assert config.temperature == 0.2
    assert config.openai_api_key is None


@patch("codereview.config.load_dotenv")
def test_config_overrides(mock_load_dotenv):
    config = Config(
        {
            "openai_api_key": "test_key",
            "default_provider": "google",
            "default_model": "gemini-2.5-flash",
            "temperature": 0.5,
        }
    )
    assert config.openai_api_key == "test_key"
    assert config.default_provider == "google"
    assert config.default_model == "gemini-2.5-flash"
    assert config.temperature == 0.5


def test_config_validate_raises():
    config = Config({"openai_api_key": None, "default_provider": "openai"})
    with pytest.raises(ValueError, match="OpenAI API Key is missing"):
        config.validate()


def test_reviewer_file_not_found():
    reviewer = Reviewer(Config({"openai_api_key": "dummy"}))
    with pytest.raises(FileNotFoundError):
        reviewer.review_file("non_existent_file_xyz.py")


@patch("codereview.llm.providers.openai.OpenAI")
def test_reviewer_success(mock_openai_class, tmp_path):
    # Setup mock client behavior
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client

    # Create structured output mock
    mock_parsed_result = ReviewResult(
        summary=Summary(
            total_issues=0,
            critical_issues=0,
            high_issues=0,
            medium_issues=0,
            low_issues=0,
            summary_text="No issues found.",
        ),
        score=Score(
            overall_score=100.0,
            security_score=100.0,
            performance_score=100.0,
            style_score=100.0,
        ),
        issues=[],
        timestamp="2026-07-03T12:00:00Z",
    )

    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(parsed=mock_parsed_result))]
    mock_client.beta.chat.completions.parse.return_value = mock_completion

    # Create a temporary file to review
    test_file = tmp_path / "test.py"
    test_file.write_text('"""Module docstring."""\nprint("hello")\n', encoding="utf-8")

    # Initialize and run reviewer
    config = Config({"openai_api_key": "fake_key"})
    reviewer = Reviewer(config)
    result = reviewer.review_file(str(test_file))

    assert isinstance(result, ReviewResult)
    assert result.score.overall_score == 100.0
    assert len(result.issues) == 0
    mock_client.beta.chat.completions.parse.assert_called_once()
