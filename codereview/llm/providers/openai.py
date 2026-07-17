from datetime import datetime
from typing import List, Optional, Dict, Set, Callable
from openai import OpenAI
from codereview.config import Config
from codereview.llm.base import BaseLLMProvider
from codereview.llm.prompts import SYSTEM_PROMPT, format_review_prompt
from codereview.models import ReviewResult, CodeContext, Issue


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, config: Config):
        self.config = config
        self.client = OpenAI(api_key=config.openai_api_key)
        self.model = config.default_model
        self.temperature = config.temperature

    def generate_review(
        self,
        code_context: CodeContext,
        static_issues: Optional[List[Issue]] = None,
        modified_lines: Optional[Set[int]] = None,
        category_focus: Optional[str] = None,
        prompt_modifier: Optional[Callable[[str], str]] = None,
    ) -> ReviewResult:
        # Check API key before sending
        self.config.validate()

        user_prompt = format_review_prompt(
            code_context, static_issues, modified_lines, category_focus
        )
        if prompt_modifier:
            user_prompt = prompt_modifier(user_prompt)

        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=ReviewResult,
                temperature=self.temperature,
                max_completion_tokens=2000,  # Cap generation length to prevent runaway repetition loops
            )

            parsed_result = completion.choices[0].message.parsed
            if parsed_result is None:
                raise ValueError("Failed to parse structured output from OpenAI.")

            # Ensure timestamp is filled
            if not parsed_result.timestamp:
                parsed_result.timestamp = datetime.utcnow().isoformat() + "Z"

            return parsed_result

        except Exception as e:
            raise RuntimeError(f"OpenAI review API call failed: {str(e)}")

    def generate_repo_summary(
        self,
        folder_structure: str,
        dependency_map: Dict[str, List[str]],
        repo_issues: List[Issue],
        file_summaries: List[str],
    ) -> Dict[str, str]:
        self.config.validate()

        issues_str = ""
        for idx, issue in enumerate(repo_issues, start=1):
            issues_str += f"  {idx}. [{issue.category.upper()} - {issue.severity.upper()}] {issue.title}: {issue.description}\n"

        file_summaries_str = "\n".join(file_summaries)

        user_prompt = f"""
Please analyze the following repository details and generate:
1. A high-level executive summary of the repository findings.
2. A detailed architecture overview highlighting patterns, design, modularity, and potential systemic issues.

--- Folder Structure Tree ---
{folder_structure}

--- Internal Dependency Map ---
{dependency_map}

--- Repository-Level Cross-File Issues ---
{issues_str or "  None"}

--- Individual File Summaries ---
{file_summaries_str}

Format your output as a JSON object containing precisely two keys:
- 'summary_text': a string containing the high-level executive summary.
- 'architecture_overview': a string containing the detailed architecture overview.
"""

        from pydantic import BaseModel

        class RepoSummaryFormat(BaseModel):
            summary_text: str
            architecture_overview: str

        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior software architect. Analyze the repository structure and summary of findings to provide a professional overview.",
                    },
                    {"role": "user", "content": user_prompt},
                ],
                response_format=RepoSummaryFormat,
                temperature=self.temperature,
                max_completion_tokens=1500,
            )

            parsed = completion.choices[0].message.parsed
            if parsed is None:
                raise ValueError(
                    "Failed to parse structured repository summary from OpenAI."
                )

            return {
                "summary_text": parsed.summary_text,
                "architecture_overview": parsed.architecture_overview,
            }
        except Exception as e:
            raise RuntimeError(f"OpenAI repository summary API call failed: {str(e)}")
