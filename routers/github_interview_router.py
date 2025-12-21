# routers/github_interview_router.py
from fastapi import APIRouter
import schemas  # 메인 스키마 임포트

# 서비스 로직 임포트 (경로가 services.githubInterview로 바뀜)
from services.githubInterview.service import create_interview_question, grade_interview_answer

router = APIRouter(
    prefix="/github-interview", 
    tags=["GitHub Interview"]
)

@router.post("/question")
def question(req: schemas.QuestionReq): # schemas. 클래스 사용
    return create_interview_question(req)

@router.post("/grade")
def grade(req: schemas.GradeReq): # schemas. 클래스 사용
    return grade_interview_answer(req)