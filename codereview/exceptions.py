class CodivusError(Exception):
    """Base exception for all Codivus errors."""

    pass


class ParserError(CodivusError):
    """Raised when code parsing fails."""

    pass


class StaticAnalysisError(CodivusError):
    """Raised when static analysis rules execution fails."""

    pass


class LLMProviderError(CodivusError):
    """Raised when LLM api calls fail."""

    pass
