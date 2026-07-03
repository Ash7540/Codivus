from typing import List
from pydantic import BaseModel
from codereview.models.summary import Summary
from codereview.models.score import Score
from codereview.models.issue import Issue

class ReviewResult(BaseModel):
    summary: Summary
    score: Score
    issues: List[Issue]
    timestamp: str
