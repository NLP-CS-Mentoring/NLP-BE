from fastapi import APIRouter, Query, Depends, HTTPException, Cookie, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .random_service import get_random_question, check_answer

# ✅ users 쪽 deps/crud/db 가져오기
from users import crud as users_crud
from users.deps import get_db, get_current_user

router = APIRouter()


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


class AnswerRequest(BaseModel):
    id: str
    user_answer: str


@router.post("/check-answer")
def check_answer_api(
    payload: AnswerRequest,
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
    from .topic_service import get_question_by_topic

    result = get_question_by_topic(topic)
    if result is None:
        return {"message": f"Topic '{topic}' 에 해당하는 문제가 없습니다."}
    return result