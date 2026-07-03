from pydantic import BaseModel

class Suggestion(BaseModel):
    original_code: str
    proposed_code: str
    explanation: str
