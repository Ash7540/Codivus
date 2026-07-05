from datetime import datetime
from typing import List, Optional
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

    def generate_review(self, code_context: CodeContext, static_issues: Optional[List[Issue]] = None) -> ReviewResult:
        # Check API key before sending
        self.config.validate()
        
        user_prompt = format_review_prompt(code_context, static_issues)
        
        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=ReviewResult,
                temperature=self.temperature,
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
