import os
import sys
import pytest
import logging
from unittest.mock import patch, MagicMock
from codereview.config import Config
from codereview.reviewer import Reviewer
from codereview.utils.cache import ReviewCache
from codereview.utils.logging import get_logger
from codereview.utils.telemetry import time_operation
from codereview.exceptions import ParserError, StaticAnalysisError, LLMProviderError, CodivusError
from codereview.models import ReviewResult, Summary, Score

@pytest.fixture
def dummy_result():
    return ReviewResult(
        summary=Summary(
            total_issues=0,
            critical_issues=0,
            high_issues=0,
            medium_issues=0,
            low_issues=0,
            summary_text="OK"
        ),
        score=Score(
            overall_score=100.0,
            security_score=100.0,
            performance_score=100.0,
            style_score=100.0
        ),
        issues=[],
        timestamp="2026-07-16T12:00:00Z"
    )

def test_cache_hits_and_bypasses(tmp_path, dummy_result):
    cache_dir = tmp_path / "cache"
    target_file = tmp_path / "file.py"
    target_file.write_text("print('hello')", encoding="utf-8")
    
    # 1. Setup config and mock provider
    config = Config(overrides={"default_provider": "mock"})
    reviewer = Reviewer(config)
    reviewer.cache = ReviewCache(cache_dir=str(cache_dir))
    
    mock_generate = MagicMock(return_value=dummy_result)
    reviewer.provider.generate_review = mock_generate
    
    # 2. First review: cache miss, calls LLM
    res1 = reviewer.review_file(str(target_file))
    assert mock_generate.call_count == 1
    
    # 3. Second review: cache hit, bypasses LLM
    res2 = reviewer.review_file(str(target_file))
    assert mock_generate.call_count == 1  # Still 1 call!
    assert res1.score.overall_score == res2.score.overall_score
    
    # 4. Cache bypass via env var
    with patch.dict(os.environ, {"CODIVUS_NO_CACHE": "1"}):
        reviewer.cache = ReviewCache(cache_dir=str(cache_dir))
        res3 = reviewer.review_file(str(target_file))
        assert mock_generate.call_count == 2  # New call triggered!
        assert res1.score.overall_score == res3.score.overall_score


def test_custom_exception_wrapping(tmp_path):
    config = Config(overrides={"default_provider": "mock"})
    reviewer = Reviewer(config)
    
    # Bypass cache to trigger execution steps
    with patch.dict(os.environ, {"CODIVUS_NO_CACHE": "1"}):
        reviewer.cache = ReviewCache()
        
        target_file = tmp_path / "test.py"
        target_file.write_text("x = 1", encoding="utf-8")

        # 1. Test ParserError (e.g. read exception)
        with pytest.raises(ParserError):
            with patch("builtins.open", side_effect=IOError("Permission denied")):
                reviewer.review_file(str(target_file))
                
        # 2. Test StaticAnalysisError
        with pytest.raises(StaticAnalysisError):
            with patch("codereview.reviewer.run_static_analysis", side_effect=Exception("AST Error")):
                reviewer.review_file(str(target_file))
                
        # 3. Test LLMProviderError
        with pytest.raises(LLMProviderError):
            reviewer.provider.generate_review = MagicMock(side_effect=Exception("API Error"))
            reviewer.review_file(str(target_file))


def test_telemetry_timing_logging():
    logger = get_logger("codivus.telemetry")
    
    with patch.object(logger, "info") as mock_info:
        with time_operation("Test Timing"):
            pass
        mock_info.assert_called_once()
        assert "Test Timing" in mock_info.call_args[0][0]


def test_logger_verbosity_level():
    with patch.dict(os.environ, {"CODIVUS_LOG_LEVEL": "DEBUG"}):
        # Trigger clean logger get
        logger = get_logger("codivus.test_debug")
        assert logger.level == logging.DEBUG
