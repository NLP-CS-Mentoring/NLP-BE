# csInterview/random_service.py
from .chroma_client import get_collection
import difflib
import numpy as np
from sentence_transformers import SentenceTransformer

from .chroma_client import get_collection

collection = get_collection()

semantic_model = SentenceTransformer("all-MiniLM-L6-v2")

_ALL_Q = collection.get()
_IDS = _ALL_Q.get("ids", []) or []
_DOCS = _ALL_Q.get("documents", []) or []
_METAS = _ALL_Q.get("metadatas", []) or []

_ID_TO_META = {id_: meta for id_, meta in zip(_IDS, _METAS)}
_ID_TO_QUESTION = {id_: doc for id_, doc in zip(_IDS, _DOCS)}


def semantic_similarity(text1: str, text2: str) -> float:
    """SentenceTransformer 임베딩으로 코사인 유사도 계산 (0.0 ~ 1.0)"""
    t1 = (text1 or "").strip()
    t2 = (text2 or "").strip()
    if not t1 or not t2:
        return 0.0

    emb1 = semantic_model.encode([t1])[0]  # shape (dim,)
    emb2 = semantic_model.encode([t2])[0]

    # 코사인 유사도 = (a · b) / (||a|| * ||b||)
    dot = float(np.dot(emb1, emb2))
    norm1 = float(np.linalg.norm(emb1))
    norm2 = float(np.linalg.norm(emb2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)

def reload_questions():
    global _ALL_Q, _IDS, _DOCS, _METAS, _ID_TO_META, _ID_TO_QUESTION
    _ALL_Q = collection.get()
    _IDS = _ALL_Q.get("ids", []) or []
    _DOCS = _ALL_Q.get("documents", []) or []
    _METAS = _ALL_Q.get("metadatas", []) or []
    _ID_TO_META = {id_: meta for id_, meta in zip(_IDS, _METAS)}
    _ID_TO_QUESTION = {id_: doc for id_, doc in zip(_IDS, _DOCS)}


def _filter_ids_by_topic(topic: str | None):
    if not topic:
        return list(_IDS)

    return [
        id_
        for id_ in _IDS
        if (_ID_TO_META.get(id_) or {}).get("topic") == topic
    ]


def get_random_question(topic: str | None = None):
    import random

    candidates = _filter_ids_by_topic(topic)
    if not candidates:
        return None

    qid = random.choice(candidates)
    q = _ID_TO_QUESTION.get(qid)
    meta = _ID_TO_META.get(qid) or {}

    return {
        "id": qid,
        "question": q,
        "topic": meta.get("topic"),
        "file": meta.get("file"),
    }


def check_answer(question_id: str, user_answer: str):
    meta = _ID_TO_META.get(question_id)
    question = _ID_TO_QUESTION.get(question_id)

    if meta is None or question is None:
        return None

    # ✅ 메타데이터 구조에 따라 채점용 정답 가져오기
    # answer_core 가 있으면 그걸 쓰고, 없으면 answer, 그것도 없으면 빈 문자열
    core_answer = (
        meta.get("answer_core")
        or meta.get("answer")
        or meta.get("correct_answer")
        or ""
    ).strip()

    full_answer = (meta.get("answer_full") or core_answer).strip()

    ua = (user_answer or "").strip()
    ua_norm = ua.lower()
    ca_norm = core_answer.lower()

    # 1) 문자열 기반 유사도 (디버깅/참고용)
    seq_sim = (
        difflib.SequenceMatcher(a=ua_norm, b=ca_norm).ratio()
        if ua_norm and ca_norm
        else 0.0
    )

    # 2) 임베딩 기반 의미 유사도
    sem_sim = semantic_similarity(ua, core_answer)

    # ✅ 최종 정답 기준 (임베딩 유사도 기반)
    # 대충 기준: 0.75 이상이면 정답, 0.6~0.75는 애매 (부분정답 느낌)
    if sem_sim >= 0.75:
        final_correct = True
        grade = "correct"
    elif sem_sim >= 0.6:
        final_correct = False
        grade = "partial"
    else:
        final_correct = False
        grade = "wrong"

    return {
        "id": question_id,
        "question": question,
        "topic": meta.get("topic"),
        "correct_answer_core": core_answer,
        "correct_answer_full": full_answer,
        "user_answer": user_answer,
        "sequence_similarity": seq_sim,
        "semantic_similarity": sem_sim,
        "grade": grade,           # "correct" / "partial" / "wrong"
        "final_correct": final_correct,
    }