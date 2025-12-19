# users/deps.py (새 파일)
from fastapi import Depends, Header, Cookie, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from . import crud

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db),
    x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
    session_id: str | None = Cookie(default=None),
):
    sid = x_session_id or session_id
    if not sid:
        raise HTTPException(status_code=401, detail="Missing session id")

    user = crud.get_user_by_session_id(db, sid)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return user