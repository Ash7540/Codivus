import os
from typing import Optional
from codereview.config import Config
from codereview.llm.router import get_provider
from codereview.models.review import ReviewResult

class Reviewer:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.provider = get_provider(self.config.default_provider, self.config)

    def review_file(self, filepath: str) -> ReviewResult:
        """
        Reviews a single file and returns structured review results.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        if not os.path.isfile(filepath):
            raise ValueError(f"Path is not a file: {filepath}")
            
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                code_content = f.read()
        except Exception as e:
            raise RuntimeError(f"Failed to read file {filepath}: {str(e)}")

        filename = os.path.basename(filepath)
        return self.provider.generate_review(code_content, filename)
