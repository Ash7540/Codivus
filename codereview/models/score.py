from pydantic import BaseModel


class Score(BaseModel):
    overall_score: float  # 0 to 100
    security_score: float
    performance_score: float
    style_score: float
