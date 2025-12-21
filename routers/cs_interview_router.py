# routers/cs_interview_router.py
from fastapi import APIRouter, Query, Depends, HTTPException, status
from sqlalchemy.orm import Session

# [스키마 임포트]
import schemas

# [서비스 로직 임포트] (경로가 services.csInterview로 바뀜 ★)
from services.csInterview.random_service import get_random_question, check_answer
from services.csInterview.topic_service import get_question_by_topic

# [Users 모듈 임포트] (users는 보통 루트에 있으므로 그대로 둠)
from users import crud as users_crud
from users.deps import get_db, get_current_user

# ★ 라우터 설정 (prefix와 tag 추가)
router = APIRouter(
    prefix="/cs-interview", 
    tags=["CS Interview"]
)

@router.get("/random-question")
def random_question(
    topic: str | None = Query(
        default=None,
        description="예: Operating System, Network, Database, Data Structure / Algorithm, Design / Architecture, Frontend, General CS",
    )
):
    data = get_random_question(topic)
    if not data:
        if topic:
            return {"message": f"'{topic}' 토픽의 질문이 없습니다."}
        return {"message": "질문 데이터가 없습니다. 먼저 인덱싱을 수행하세요."}
    return data

@router.post("/check-answer")
def check_answer_api(
    payload: schemas.AnswerRequest, # ★ schemas에 정의된 모델 사용
    db: Session = Depends(get_db),
    me = Depends(get_current_user),
):
    result = check_answer(payload.id, payload.user_answer)
    if not result:
        raise HTTPException(status_code=404, detail="문제 없음")

    topic = result.get("topic")
    is_correct = bool(result.get("final_correct"))

    if topic:
        users_crud.update_user_topic_stats(
            db,
            user_id=me.id,
            topic=topic,
            is_correct=is_correct,
        )
    return result

@router.get("/question-by-topic")
def question_by_topic(topic: str):
    result = get_question_by_topic(topic)
    if result is None:
        return {"message": f"Topic '{topic}' 에 해당하는 문제가 없습니다."}
    return result