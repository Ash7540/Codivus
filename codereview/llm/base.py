from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Set, Callable
from codereview.models.review import ReviewResult
from codereview.models.structure import CodeContext
from codereview.models.issue import Issue


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_review(
        self,
        code_context: CodeContext,
        static_issues: Optional[List[Issue]] = None,
        modified_lines: Optional[Set[int]] = None,
        category_focus: Optional[str] = None,
        prompt_modifier: Optional[Callable[[str], str]] = None,
    ) -> ReviewResult:
        """
        Sends parsed code context and optional static analysis findings to the LLM provider and returns a structured ReviewResult.
        """
        pass

    @abstractmethod
    def generate_repo_summary(
        self,
        folder_structure: str,
        dependency_map: Dict[str, List[str]],
        repo_issues: List[Issue],
        file_summaries: List[str],
    ) -> Dict[str, str]:
        """
        Generates a high-level summary and architecture overview for the entire repository.
        Returns a dict with 'summary_text' and 'architecture_overview'.
        """
        pass
