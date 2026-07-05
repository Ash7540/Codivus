from abc import ABC, abstractmethod
from typing import List
from codereview.models.issue import Issue
from codereview.models.structure import CodeContext

class BaseAnalyzer(ABC):
    @abstractmethod
    def analyze(self, context: CodeContext) -> List[Issue]:
        """
        Analyzes the given CodeContext and returns a list of detected issues.
        """
        pass
