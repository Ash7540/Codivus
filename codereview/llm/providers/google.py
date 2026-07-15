import json
import os
from typing import List, Optional, Dict, Set, Callable
from codereview.config import Config
from codereview.llm.base import BaseLLMProvider
from codereview.llm.prompts import SYSTEM_PROMPT, format_review_prompt
from codereview.models import ReviewResult, CodeContext, Issue

try:
    import google.generativeai as genai
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False

class GoogleProvider(BaseLLMProvider):
    def __init__(self, config: Config):
        self.config = config
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model = os.getenv("CODIVUS_MODEL", "gemini-1.5-pro")
        
        if HAS_GOOGLE and self.api_key:
            import google.generativeai as genai
            self.genai = genai
            self.genai.configure(api_key=self.api_key)
        else:
            self.genai = None

    def _validate(self):
        if not HAS_GOOGLE:
            raise ImportError(
                "Google Gemini provider requires the 'google-generativeai' package. "
                "Please install it using 'pip install google-generativeai'."
            )
        if not self.api_key:
            raise ValueError(
                "Gemini API Key is missing. Please set GEMINI_API_KEY (or GOOGLE_API_KEY) in your environment or .env file."
            )
        if not self.genai:
            import google.generativeai as genai
            self.genai = genai
            self.genai.configure(api_key=self.api_key)

    def generate_review(
        self, 
        code_context: CodeContext, 
        static_issues: Optional[List[Issue]] = None,
        modified_lines: Optional[Set[int]] = None,
        category_focus: Optional[str] = None,
        prompt_modifier: Optional[Callable[[str], str]] = None
    ) -> ReviewResult:
        self._validate()
        
        user_prompt = format_review_prompt(code_context, static_issues, modified_lines, category_focus)
        if prompt_modifier:
            user_prompt = prompt_modifier(user_prompt)
        
        try:
            model = self.genai.GenerativeModel(
                model_name=self.model,
                system_instruction=SYSTEM_PROMPT
            )
            config = self.genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=self.config.temperature
            )
            response = model.generate_content(
                user_prompt,
                generation_config=config
            )
            data = json.loads(response.text)
            return ReviewResult.model_validate(data)
        except Exception as e:
            raise RuntimeError(f"Gemini API call failed: {str(e)}")

    def generate_repo_summary(
        self,
        folder_structure: str,
        dependency_map: Dict[str, List[str]],
        repo_issues: List[Issue],
        file_summaries: List[str]
    ) -> Dict[str, str]:
        self._validate()
        
        prompt = f"""
Analyze the following repository metadata and generate:
1. A high-level executive summary of findings ('summary_text').
2. An architecture overview of the project structure and dependencies ('architecture_overview').

Folder Structure:
{folder_structure}

Dependency Map:
{json.dumps(dependency_map, indent=2)}

Repository-level issues:
{json.dumps([i.model_dump() for i in repo_issues], indent=2, default=str)}

Individual File Summaries:
{chr(10).join(file_summaries)}

Return your output as a JSON object containing keys: 'summary_text' and 'architecture_overview'.
"""
        try:
            model = self.genai.GenerativeModel(
                model_name=self.model,
                system_instruction="You are a repo summary expert. Return ONLY a valid JSON object matching the requested schema."
            )
            config = self.genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
            response = model.generate_content(
                prompt,
                generation_config=config
            )
            data = json.loads(response.text)
            return {
                "summary_text": data.get("summary_text", "No summary generated."),
                "architecture_overview": data.get("architecture_overview", "No architecture overview generated.")
            }
        except Exception as e:
            raise RuntimeError(f"Gemini API call failed: {str(e)}")
