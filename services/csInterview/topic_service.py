import random
from .random_service import _ID_TO_META, _ID_TO_QUESTION

def get_question_by_topic(topic: str):
    """
    주어진 topic을 가진 문제 중 하나를 랜덤으로 반환
    """
    # topic 일치하는 문제들 찾기
    candidates = [
        qid for qid, meta in _ID_TO_META.items()
        if meta["topic"].lower() == topic.lower()
    ]

    if not candidates:
        return None

    picked_id = random.choice(candidates)

    return {
        "id": picked_id,
        "question": _ID_TO_QUESTION[picked_id],
        "topic": topic
    }