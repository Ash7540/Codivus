import json
import os
from typing import List, Optional, Dict, Set, Callable
from codereview.config import Config
from codereview.llm.base import BaseLLMProvider
from codereview.llm.prompts import SYSTEM_PROMPT, format_review_prompt
from codereview.models import ReviewResult, CodeContext, Issue


class AzureProvider(BaseLLMProvider):
    def __init__(self, config: Config):
        self.config = config
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        self.deployment_name = os.getenv("CODIVUS_MODEL") or os.getenv(
            "AZURE_OPENAI_DEPLOYMENT_NAME"
        )
        self.client = None

        if self.api_key and self.endpoint:
            from openai import AzureOpenAI

            self.client = AzureOpenAI(
                azure_endpoint=self.endpoint,
                api_key=self.api_key,
                api_version=self.api_version,
            )

    def _validate(self):
        if not self.api_key or not self.endpoint:
            raise ValueError(
                "Azure OpenAI configuration is missing. "
                "Please set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT in your environment or .env file."
            )
        if not self.deployment_name:
            raise ValueError(
                "Azure OpenAI deployment name is missing. "
                "Please set CODIVUS_MODEL or AZURE_OPENAI_DEPLOYMENT_NAME to select your deployed model name."
            )
        if not self.client:
            from openai import AzureOpenAI

            self.client = AzureOpenAI(
                azure_endpoint=self.endpoint,
                api_key=self.api_key,
                api_version=self.api_version,
            )

    def generate_review(
        self,
        code_context: CodeContext,
        static_issues: Optional[List[Issue]] = None,
        modified_lines: Optional[Set[int]] = None,
        category_focus: Optional[str] = None,
        prompt_modifier: Optional[Callable[[str], str]] = None,
    ) -> ReviewResult:
        self._validate()

        user_prompt = format_review_prompt(
            code_context, static_issues, modified_lines, category_focus
        )
        if prompt_modifier:
            user_prompt = prompt_modifier(user_prompt)

        try:
            completion = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.config.temperature,
                response_format={"type": "json_object"},
            )
            response_text = completion.choices[0].message.content
            data = json.loads(response_text)
            return ReviewResult.model_validate(data)
        except Exception as e:
            raise RuntimeError(f"Azure OpenAI API call failed: {str(e)}")

    def generate_repo_summary(
        self,
        folder_structure: str,
        dependency_map: Dict[str, List[str]],
        repo_issues: List[Issue],
        file_summaries: List[str],
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
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a repository analyzer. You MUST output ONLY a valid JSON object matching the requested schema.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            response_text = completion.choices[0].message.content
            data = json.loads(response_text)
            return {
                "summary_text": data.get("summary_text", "No summary generated."),
                "architecture_overview": data.get(
                    "architecture_overview", "No architecture overview generated."
                ),
            }
        except Exception as e:
            raise RuntimeError(f"Azure OpenAI API call failed: {str(e)}")
