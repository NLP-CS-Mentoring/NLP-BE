from fastapi import APIRouter
import schemas  

from services.githubInterview.service import create_interview_question, grade_interview_answer

router = APIRouter(
    prefix="/github-interview", 
    tags=["GitHub Interview"]
)

@router.post("/question")
def question(req: schemas.QuestionReq): 
    return create_interview_question(req)

@router.post("/grade")
def grade(req: schemas.GradeReq): 
    return grade_interview_answer(req)