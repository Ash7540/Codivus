from codereview.config import Config
from codereview.llm.base import BaseLLMProvider
from codereview.llm.providers.openai import OpenAIProvider
from codereview.llm.providers.mock import MockProvider

def get_provider(provider_name: str, config: Config) -> BaseLLMProvider:
    provider_name_lower = provider_name.lower()
    if provider_name_lower == "openai":
        return OpenAIProvider(config)
    elif provider_name_lower == "mock":
        return MockProvider(config)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider_name}")
