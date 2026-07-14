import json
import os
from typing import List, Optional, Dict, Set
from codereview.config import Config
from codereview.llm.base import BaseLLMProvider
from codereview.llm.prompts import SYSTEM_PROMPT, format_review_prompt
from codereview.models import ReviewResult, CodeContext, Issue

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

class AnthropicProvider(BaseLLMProvider):
    def __init__(self, config: Config):
        self.config = config
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = os.getenv("CODIVUS_MODEL", "claude-3-5-sonnet-20240620")
        
        if HAS_ANTHROPIC and self.api_key:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None

    def _validate(self):
        if not HAS_ANTHROPIC:
            raise ImportError(
                "Anthropic provider requires the 'anthropic' package. "
                "Please install it using 'pip install anthropic'."
            )
        if not self.api_key:
            raise ValueError(
                "Anthropic API Key is missing. Please set ANTHROPIC_API_KEY in your environment or .env file."
            )

    def _clean_json_response(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    def generate_review(
        self, 
        code_context: CodeContext, 
        static_issues: Optional[List[Issue]] = None,
        modified_lines: Optional[Set[int]] = None,
        category_focus: Optional[str] = None
    ) -> ReviewResult:
        self._validate()
        
        user_prompt = format_review_prompt(code_context, static_issues, modified_lines, category_focus)
        system_instruction = SYSTEM_PROMPT + "\nCRITICAL: Return ONLY a valid JSON object matching the requested schema. Do not wrap in markdown tags or include any explanation outside the JSON."

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=self.config.temperature,
                system=system_instruction,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            response_text = self._clean_json_response(message.content[0].text)
            data = json.loads(response_text)
            return ReviewResult.model_validate(data)
        except Exception as e:
            raise RuntimeError(f"Anthropic API call failed: {str(e)}")

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
        system_instruction = "Return ONLY a valid JSON object matching the requested schema. Do not write markdown wrappers."

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.2,
                system=system_instruction,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            response_text = self._clean_json_response(message.content[0].text)
            data = json.loads(response_text)
            return {
                "summary_text": data.get("summary_text", "No summary generated."),
                "architecture_overview": data.get("architecture_overview", "No architecture overview generated.")
            }
        except Exception as e:
            raise RuntimeError(f"Anthropic API call failed: {str(e)}")
