from fastapi import APIRouter
from .schemas import QuestionReq, GradeReq
from .service import create_interview_question, grade_interview_answer

router = APIRouter(prefix="/github-interview", tags=["GitHub Interview"])

@router.post("/question")
def question(req: QuestionReq):
    return create_interview_question(req)

@router.post("/grade")
def grade(req: GradeReq):
    return grade_interview_answer(req)