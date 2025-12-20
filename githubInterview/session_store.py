import uuid

_SESSIONS: dict[str, dict] = {}

def save_session(question_pack: dict, meta: dict | None = None) -> str:
    session_id = str(uuid.uuid4())
    _SESSIONS[session_id] = {
        "question_pack": question_pack,
        "meta": meta or {},
    }
    return session_id

def get_session(session_id: str) -> dict | None:
    return _SESSIONS.get(session_id)