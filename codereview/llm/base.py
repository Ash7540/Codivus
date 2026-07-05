from abc import ABC, abstractmethod
from typing import List, Optional
from codereview.models.review import ReviewResult
from codereview.models.structure import CodeContext
from codereview.models.issue import Issue

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_review(self, code_context: CodeContext, static_issues: Optional[List[Issue]] = None) -> ReviewResult:
        """
        Sends parsed code context and optional static analysis findings to the LLM provider and returns a structured ReviewResult.
        """
        pass
