from typing import Optional
from pydantic import BaseModel
from codereview.models.suggestion import Suggestion

class Issue(BaseModel):
    title: str
    description: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    category: str  # 'bug', 'style', 'performance', 'security'
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    suggestion: Optional[Suggestion] = None
