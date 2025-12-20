# users/userApi.py
from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, status
from sqlalchemy.orm import Session

from database import SessionLocal
from . import crud, schemas

router = APIRouter(prefix="/users", tags=["users"])


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    session_id: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    if session_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user = crud.get_user_by_session_id(db, session_id=session_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    return user


# ✅ 회원가입
@router.post("/", response_model=schemas.User, summary="회원가입")
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)


# ✅ 로그인(JSON)
@router.post("/login", summary="로그인(JSON)")
def login(payload: schemas.LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=payload.username)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    from . import security
    if not security.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    session = crud.create_user_session(db, user_id=user.id)

    # ✅ 세션을 쿠키로 내려줌 (바디는 없어도 됨)
    response.set_cookie(
        key="session_id",
        value=session.session_id,
        httponly=True,
        samesite="lax",
        secure=False,  # 로컬 http면 False (https 배포시 True)
        max_age=60 * 60 * 24 * 7,
        path="/",
    )
    return {"ok": True}

@router.post("/logout", summary="로그아웃")
def logout(response: Response, session_id: str | None = Cookie(None), db: Session = Depends(get_db)):
    if session_id:
        crud.delete_session_by_id(db, session_id=session_id)
    response.delete_cookie(key="session_id")
    return {"message": "Logout successful"}


@router.get("/me", response_model=schemas.User, summary="내 정보")
def read_users_me(me=Depends(get_current_user)):
    return me


@router.get("/me/topic-stats", response_model=list[schemas.UserTopicStatResponse], summary="내 토픽별 통계")
def get_my_topic_stats(
    db: Session = Depends(get_db),
    me=Depends(get_current_user),
):
    stats = crud.list_user_topic_stats(db, me.id)

    res = []
    for s in stats:
        wrong_rate = (s.wrong_count / s.attempt_count) if s.attempt_count else 0.0
        res.append(
            schemas.UserTopicStatResponse(
                topic=s.topic,
                attempt_count=s.attempt_count,
                correct_count=s.correct_count,
                wrong_count=s.wrong_count,
                wrong_rate=wrong_rate,
                last_attempt_at=s.last_attempt_at,
            )
        )
    return res