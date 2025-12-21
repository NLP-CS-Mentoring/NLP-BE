from pydantic import BaseModel

class QuestionReq(BaseModel):
    repo_url: str
    difficulty: str = "mid"  # junior|mid|senior

class GradeReq(BaseModel):
    session_id: str
    answer: str