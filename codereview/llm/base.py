from abc import ABC, abstractmethod
from codereview.models.review import ReviewResult
from codereview.models.structure import CodeContext

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_review(self, code_context: CodeContext) -> ReviewResult:
        """
        Sends parsed code context to the LLM provider and returns a structured ReviewResult.
        """
        pass
