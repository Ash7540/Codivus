import json
import os
from typing import List, Optional, Dict, Set, Callable
from codereview.config import Config
from codereview.llm.base import BaseLLMProvider
from codereview.llm.prompts import SYSTEM_PROMPT, format_review_prompt
from codereview.models import ReviewResult, CodeContext, Issue

class OpenRouterProvider(BaseLLMProvider):
    def __init__(self, config: Config):
        self.config = config
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("CODIVUS_MODEL") or os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3-70b-instruct:free")
        self.client = None
        
        if self.api_key:
            from openai import OpenAI
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key
            )

    def _validate(self):
        if not self.api_key:
            raise ValueError(
                "OpenRouter API Key is missing. Please set OPENROUTER_API_KEY in your environment or .env file."
            )
        if not self.client:
            from openai import OpenAI
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key
            )

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
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.config.temperature,
                response_format={"type": "json_object"}
            )
            response_text = completion.choices[0].message.content
            data = json.loads(response_text)
            return ReviewResult.model_validate(data)
        except Exception as e:
            raise RuntimeError(f"OpenRouter API call failed: {str(e)}")

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
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a repository analyzer. You MUST output ONLY a valid JSON object matching the requested schema."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            response_text = completion.choices[0].message.content
            data = json.loads(response_text)
            return {
                "summary_text": data.get("summary_text", "No summary generated."),
                "architecture_overview": data.get("architecture_overview", "No architecture overview generated.")
            }
        except Exception as e:
            raise RuntimeError(f"OpenRouter API call failed: {str(e)}")
