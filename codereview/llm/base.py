from abc import ABC, abstractmethod
from codereview.models.review import ReviewResult

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_review(self, code_content: str, filename: str) -> ReviewResult:
        """
        Sends code to the LLM provider and returns a structured ReviewResult.
        """
        pass
