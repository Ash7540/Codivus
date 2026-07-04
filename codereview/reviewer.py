import os
from typing import Optional
from codereview.config import Config
from codereview.llm.router import get_provider
from codereview.models.review import ReviewResult
from codereview.parsers import get_parser_for_file

class Reviewer:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.provider = get_provider(self.config.default_provider, self.config)

    def review_file(self, filepath: str) -> ReviewResult:
        """
        Reviews a single file and returns structured review results.
        """
        # Ensure filepath is absolute to have reliable paths in CodeContext
        abs_filepath = os.path.abspath(filepath)
        
        if not os.path.exists(abs_filepath):
            raise FileNotFoundError(f"File not found: {abs_filepath}")
        
        if not os.path.isfile(abs_filepath):
            raise ValueError(f"Path is not a file: {abs_filepath}")
            
        try:
            with open(abs_filepath, "r", encoding="utf-8") as f:
                code_content = f.read()
        except Exception as e:
            raise RuntimeError(f"Failed to read file {abs_filepath}: {str(e)}")

        # 1. Parse file content into CodeContext
        parser = get_parser_for_file(abs_filepath)
        code_context = parser.parse_code(code_content, abs_filepath)

        # 2. Invoke LLM provider with CodeContext
        return self.provider.generate_review(code_context)
