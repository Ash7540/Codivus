from abc import ABC, abstractmethod
from codereview.models.structure import CodeContext

class BaseParser(ABC):
    @abstractmethod
    def parse_code(self, code_content: str, file_path: str) -> CodeContext:
        """
        Parses source code content and returns a structured CodeContext.
        """
        pass
