import json
import os
import urllib.request
import urllib.error
from typing import List, Optional, Dict, Set
from codereview.config import Config
from codereview.llm.base import BaseLLMProvider
from codereview.llm.prompts import SYSTEM_PROMPT, format_review_prompt
from codereview.models import ReviewResult, CodeContext, Issue

class OllamaProvider(BaseLLMProvider):
    def __init__(self, config: Config):
        self.config = config
        self.host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip('/')
        self.model = os.getenv("CODIVUS_MODEL") or os.getenv("OLLAMA_MODEL", "llama3")

    def _query_ollama(self, system_instruction: str, user_prompt: str, temperature: float) -> str:
        url = f"{self.host}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {
                "temperature": temperature
            },
            "format": "json"
        }
        
        headers = {"Content-Type": "application/json"}
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data["message"]["content"]
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to connect to local Ollama server at {self.host}: {str(e.reason)}")
        except Exception as e:
            raise RuntimeError(f"Ollama execution failed: {str(e)}")

    def generate_review(
        self, 
        code_context: CodeContext, 
        static_issues: Optional[List[Issue]] = None,
        modified_lines: Optional[Set[int]] = None,
        category_focus: Optional[str] = None
    ) -> ReviewResult:
        user_prompt = format_review_prompt(code_context, static_issues, modified_lines, category_focus)
        
        response_text = self._query_ollama(
            system_instruction=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=self.config.temperature
        )
        data = json.loads(response_text.strip())
        return ReviewResult.model_validate(data)

    def generate_repo_summary(
        self,
        folder_structure: str,
        dependency_map: Dict[str, List[str]],
        repo_issues: List[Issue],
        file_summaries: List[str]
    ) -> Dict[str, str]:
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
        response_text = self._query_ollama(
            system_instruction="You are a repository analyzer. You MUST output ONLY a valid JSON object matching the requested schema.",
            user_prompt=prompt,
            temperature=0.2
        )
        data = json.loads(response_text.strip())
        return {
            "summary_text": data.get("summary_text", "No summary generated."),
            "architecture_overview": data.get("architecture_overview", "No architecture overview generated.")
        }
