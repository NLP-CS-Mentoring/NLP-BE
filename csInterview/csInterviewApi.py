from fastapi import APIRouter, Query
from pydantic import BaseModel

from .random_service import get_random_question, check_answer

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
def check_answer_api(payload: AnswerRequest):
    result = check_answer(payload.id, payload.user_answer)
    if not result:
        return {"message": f"ID '{payload.id}' 에 해당하는 문제가 없습니다."}
    return result


@router.get("/question-by-topic")
def question_by_topic(topic: str):
    # 기존에 topic_service를 통해 처리하던 것을 random_service와 메타데이터로 대체합니다.
    # 필요 시 topic_service의 get_question_by_topic을 import하여 사용하도록 변경 가능합니다.
    from .topic_service import get_question_by_topic

    result = get_question_by_topic(topic)
    if result is None:
        return {"message": f"Topic '{topic}' 에 해당하는 문제가 없습니다."}
    return result
