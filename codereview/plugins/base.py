from abc import ABC, abstractmethod
from typing import List, Callable
from codereview.models import CodeContext, Issue, ReviewResult


class BasePlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the unique name of the plugin."""
        pass

    def get_analysers(self) -> List[Callable[[CodeContext], List[Issue]]]:
        """Returns a list of custom code static analysers."""
        return []

    def modify_prompt(self, context: CodeContext, prompt: str) -> str:
        """Allows modifying the user prompt before sending to the LLM."""
        return prompt

    def on_review_start(self, context: CodeContext) -> None:
        """Hook called before starting review processes."""
        pass

    def on_review_end(self, context: CodeContext, result: ReviewResult) -> None:
        """Hook called after the review completes."""
        pass
