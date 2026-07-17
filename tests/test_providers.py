# ruff: noqa: E402
import os
import json
import sys
from unittest.mock import patch, MagicMock

# Define mock modules so standard imports inside the provider modules succeed
sys.modules["anthropic"] = MagicMock()
sys.modules["google"] = MagicMock()
sys.modules["google.generativeai"] = MagicMock()

import pytest
from codereview.config import Config
from codereview.llm.router import get_provider
from codereview.llm.providers import (
    OpenAIProvider,
    MockProvider,
    AnthropicProvider,
    GoogleProvider,
    OllamaProvider,
    OpenRouterProvider,
    AzureProvider,
)
from codereview.models import CodeContext, FileStats


@pytest.fixture
def dummy_context():
    return CodeContext(
        filename="a.py",
        file_path="a.py",
        source_code="print('hello')",
        imports=[],
        classes=[],
        functions=[],
        stats=FileStats(
            loc=1, comment_lines=0, blank_lines=0, num_classes=0, num_functions=0
        ),
    )


def test_router_get_provider():
    config = Config()

    # Check default/supported mappings
    assert isinstance(get_provider("openai", config), OpenAIProvider)
    assert isinstance(get_provider("mock", config), MockProvider)

    # We patch SDK indicators to instantiate without errors
    with patch("codereview.llm.providers.anthropic.HAS_ANTHROPIC", True), patch.dict(
        os.environ, {"ANTHROPIC_API_KEY": "dummy_key"}
    ):
        assert isinstance(get_provider("anthropic", config), AnthropicProvider)

    with patch("codereview.llm.providers.google.HAS_GOOGLE", True), patch.dict(
        os.environ, {"GEMINI_API_KEY": "dummy_key"}
    ):
        assert isinstance(get_provider("google", config), GoogleProvider)
        assert isinstance(get_provider("gemini", config), GoogleProvider)

    assert isinstance(get_provider("ollama", config), OllamaProvider)

    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "dummy_key"}):
        assert isinstance(get_provider("openrouter", config), OpenRouterProvider)

    with patch.dict(
        os.environ,
        {
            "AZURE_OPENAI_API_KEY": "dummy_key",
            "AZURE_OPENAI_ENDPOINT": "dummy_endpoint",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "dummy",
        },
    ):
        assert isinstance(get_provider("azure", config), AzureProvider)

    # Check error cases
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        get_provider("unsupported_provider_name", config)


@patch("codereview.llm.providers.anthropic.HAS_ANTHROPIC", False)
def test_anthropic_missing_sdk():
    config = Config()
    provider = AnthropicProvider(config)

    with pytest.raises(ImportError, match="requires the 'anthropic' package"):
        provider.generate_review(MagicMock())


@patch("codereview.llm.providers.anthropic.HAS_ANTHROPIC", True)
def test_anthropic_missing_key():
    config = Config()
    with patch.dict(os.environ, {}, clear=True):
        provider = AnthropicProvider(config)
        with pytest.raises(ValueError, match="API Key is missing"):
            provider.generate_review(MagicMock())


@patch("codereview.llm.providers.anthropic.HAS_ANTHROPIC", True)
def test_anthropic_successful_call(dummy_context):
    config = Config()
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "dummy_key"}):
        provider = AnthropicProvider(config)

        # Mock anthropic client
        mock_client = MagicMock()
        provider.client = mock_client

        # Setup mock response matching ReviewResult schema
        dummy_res_dict = {
            "summary": {
                "total_issues": 0,
                "critical_issues": 0,
                "high_issues": 0,
                "medium_issues": 0,
                "low_issues": 0,
                "summary_text": "Clean code",
            },
            "score": {
                "overall_score": 100.0,
                "security_score": 100.0,
                "performance_score": 100.0,
                "style_score": 100.0,
            },
            "issues": [],
            "timestamp": "2026-07-14T12:00:00Z",
        }

        mock_message = MagicMock()
        mock_message.content = [
            MagicMock(text=f"```json\n{json.dumps(dummy_res_dict)}\n```")
        ]
        mock_client.messages.create.return_value = mock_message

        res = provider.generate_review(dummy_context)
        assert res.score.overall_score == 100.0

        # Test generate_repo_summary
        mock_summary_message = MagicMock()
        mock_summary_message.content = [
            MagicMock(
                text=json.dumps(
                    {"summary_text": "Summary", "architecture_overview": "Arch"}
                )
            )
        ]
        mock_client.messages.create.return_value = mock_summary_message

        summary_res = provider.generate_repo_summary("Folders", {}, [], [])
        assert summary_res["summary_text"] == "Summary"


@patch("codereview.llm.providers.google.HAS_GOOGLE", False)
def test_google_missing_sdk():
    config = Config()
    provider = GoogleProvider(config)

    with pytest.raises(ImportError, match="requires the 'google-generativeai' package"):
        provider.generate_review(MagicMock())


@patch("codereview.llm.providers.google.HAS_GOOGLE", True)
def test_google_missing_key():
    config = Config()
    with patch.dict(os.environ, {}, clear=True):
        provider = GoogleProvider(config)
        with pytest.raises(ValueError, match="API Key is missing"):
            provider.generate_review(MagicMock())


@patch("codereview.llm.providers.google.HAS_GOOGLE", True)
def test_google_successful_call(dummy_context):
    config = Config()
    with patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key"}):
        provider = GoogleProvider(config)

        mock_model = MagicMock()
        provider.genai.GenerativeModel = MagicMock(return_value=mock_model)

        # Mock response matching ReviewResult schema
        dummy_res_dict = {
            "summary": {
                "total_issues": 0,
                "critical_issues": 0,
                "high_issues": 0,
                "medium_issues": 0,
                "low_issues": 0,
                "summary_text": "Good",
            },
            "score": {
                "overall_score": 90.0,
                "security_score": 90.0,
                "performance_score": 90.0,
                "style_score": 90.0,
            },
            "issues": [],
            "timestamp": "2026-07-14T12:00:00Z",
        }

        mock_response = MagicMock()
        mock_response.text = json.dumps(dummy_res_dict)
        mock_model.generate_content.return_value = mock_response

        res = provider.generate_review(dummy_context)
        assert res.score.overall_score == 90.0

        # Also test generate_repo_summary
        mock_summary_response = MagicMock()
        mock_summary_response.text = json.dumps(
            {"summary_text": "Summary", "architecture_overview": "Arch"}
        )
        mock_model.generate_content.return_value = mock_summary_response

        summary_res = provider.generate_repo_summary("Folders", {}, [], [])
        assert summary_res["summary_text"] == "Summary"


@patch("urllib.request.urlopen")
def test_ollama_successful_call(mock_urlopen, dummy_context):
    config = Config()
    provider = OllamaProvider(config)

    # Mock urllib response
    mock_resp = MagicMock()
    dummy_res_dict = {
        "summary": {
            "total_issues": 0,
            "critical_issues": 0,
            "high_issues": 0,
            "medium_issues": 0,
            "low_issues": 0,
            "summary_text": "Clean",
        },
        "score": {
            "overall_score": 95.0,
            "security_score": 95.0,
            "performance_score": 95.0,
            "style_score": 95.0,
        },
        "issues": [],
        "timestamp": "2026-07-14T12:00:00Z",
    }

    ollama_api_resp = {"message": {"content": json.dumps(dummy_res_dict)}}
    mock_resp.read.return_value = json.dumps(ollama_api_resp).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    res = provider.generate_review(dummy_context)
    assert res.score.overall_score == 95.0


def test_openrouter_missing_key():
    config = Config()
    with patch.dict(os.environ, {}, clear=True):
        provider = OpenRouterProvider(config)
        with pytest.raises(ValueError, match="API Key is missing"):
            provider.generate_review(MagicMock())


@patch("openai.OpenAI")
def test_openrouter_successful_call(mock_openai_class, dummy_context):
    config = Config()
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "dummy_key"}):
        provider = OpenRouterProvider(config)

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        provider.client = mock_client

        dummy_res_dict = {
            "summary": {
                "total_issues": 0,
                "critical_issues": 0,
                "high_issues": 0,
                "medium_issues": 0,
                "low_issues": 0,
                "summary_text": "Good",
            },
            "score": {
                "overall_score": 85.0,
                "security_score": 85.0,
                "performance_score": 85.0,
                "style_score": 85.0,
            },
            "issues": [],
            "timestamp": "2026-07-14T12:00:00Z",
        }

        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content=json.dumps(dummy_res_dict)))
        ]
        mock_client.chat.completions.create.return_value = mock_completion

        res = provider.generate_review(dummy_context)
        assert res.score.overall_score == 85.0


def test_azure_missing_config():
    config = Config()
    # Missing endpoint or key
    with patch.dict(os.environ, {}, clear=True):
        provider = AzureProvider(config)
        with pytest.raises(ValueError, match="Azure OpenAI configuration is missing"):
            provider.generate_review(MagicMock())

    # Missing deployment name
    with patch.dict(
        os.environ,
        {"AZURE_OPENAI_API_KEY": "k", "AZURE_OPENAI_ENDPOINT": "e"},
        clear=True,
    ):
        provider = AzureProvider(config)
        with pytest.raises(ValueError, match="deployment name is missing"):
            provider.generate_review(MagicMock())


@patch("openai.AzureOpenAI")
def test_azure_successful_call(mock_azure_class, dummy_context):
    config = Config()
    env = {
        "AZURE_OPENAI_API_KEY": "dummy_key",
        "AZURE_OPENAI_ENDPOINT": "dummy_endpoint",
        "AZURE_OPENAI_DEPLOYMENT_NAME": "dummy_deployment",
    }
    with patch.dict(os.environ, env):
        provider = AzureProvider(config)

        mock_client = MagicMock()
        mock_azure_class.return_value = mock_client
        provider.client = mock_client

        dummy_res_dict = {
            "summary": {
                "total_issues": 0,
                "critical_issues": 0,
                "high_issues": 0,
                "medium_issues": 0,
                "low_issues": 0,
                "summary_text": "Good",
            },
            "score": {
                "overall_score": 92.0,
                "security_score": 92.0,
                "performance_score": 92.0,
                "style_score": 92.0,
            },
            "issues": [],
            "timestamp": "2026-07-14T12:00:00Z",
        }

        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content=json.dumps(dummy_res_dict)))
        ]
        mock_client.chat.completions.create.return_value = mock_completion

        res = provider.generate_review(dummy_context)
        assert res.score.overall_score == 92.0
