from typing import List, Dict, Optional
from pydantic import BaseModel
from codereview.models.summary import Summary
from codereview.models.score import Score
from codereview.models.issue import Issue

class ReviewResult(BaseModel):
    summary: Summary
    score: Score
    issues: List[Issue]
    timestamp: str

class RepositorySummary(BaseModel):
    total_files: int
    total_loc: int
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    summary_text: str

class RepositoryReviewResult(BaseModel):
    summary: RepositorySummary
    overall_score: Score
    file_reviews: Dict[str, ReviewResult]
    repo_issues: List[Issue]
    architecture_overview: Optional[str] = None
    folder_structure: str
    timestamp: str

