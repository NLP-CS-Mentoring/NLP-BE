from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# === [자소서 관련] ===
class BasicRequest(BaseModel):
    user_fact: str

# === [뉴스 RAG 관련] ===
class NewsReportResponse(BaseModel):
    report: Dict[str, Any]

class NewsRequest(BaseModel):
    interest: str

class ArticleResponse(BaseModel):
    title: str
    link: str
    preview: str
    pubDate: Optional[str] = None

# === [커리어 RAG 관련] ===
class CareerRequest(BaseModel):
    query: str 

class CareerResponse(BaseModel):
    advice: str

# === [CS 인터뷰 관련] ===
class AnswerRequest(BaseModel):
    id: str
    user_answer: str

# === [GitHub 인터뷰 관련] ===
class QuestionReq(BaseModel):
    repo_url: str
    difficulty: str = "mid"  # junior|mid|senior

class GradeReq(BaseModel):
    session_id: str
    answer: str