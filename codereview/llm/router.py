from codereview.config import Config
from codereview.llm.base import BaseLLMProvider
from codereview.llm.providers import (
    OpenAIProvider,
    MockProvider,
    AnthropicProvider,
    GoogleProvider,
    OllamaProvider,
    OpenRouterProvider,
    AzureProvider,
)

def get_provider(provider_name: str, config: Config) -> BaseLLMProvider:
    provider_name_lower = provider_name.lower()
    if provider_name_lower == "openai":
        return OpenAIProvider(config)
    elif provider_name_lower == "mock":
        return MockProvider(config)
    elif provider_name_lower == "anthropic":
        return AnthropicProvider(config)
    elif provider_name_lower in ("google", "gemini"):
        return GoogleProvider(config)
    elif provider_name_lower == "ollama":
        return OllamaProvider(config)
    elif provider_name_lower == "openrouter":
        return OpenRouterProvider(config)
    elif provider_name_lower == "azure":
        return AzureProvider(config)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider_name}")
