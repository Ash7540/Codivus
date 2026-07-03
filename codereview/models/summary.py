from pydantic import BaseModel

class Summary(BaseModel):
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    summary_text: str
