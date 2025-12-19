from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from . import crud, models, schemas, security
from database import SessionLocal

router = APIRouter(prefix="/users", tags=["users"])


# Dependency: 각 API 요청마다 DB 세션 생성/종료
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency: 쿠키로부터 현재 사용자 가져오기
def get_current_user(
    session_id: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    if session_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    user = crud.get_user_by_session_id(db, session_id=session_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        )
    return user


# ✅ 토픽 통계 조회
@router.get("/me/topic-stats", response_model=list[schemas.UserTopicStatResponse])
def get_my_topic_stats(
    db: Session = Depends(get_db),
    me: models.User = Depends(get_current_user),
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


@router.post("/login")
def login(payload: schemas.LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=payload.username)
    if not user or not security.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    session = crud.create_user_session(db, user_id=user.id)

    max_age = 60 * 60 * 24 * 7

    response.set_cookie(
        key="session_id",
        value=session.session_id,
        httponly=True,
        max_age=max_age,  
        samesite="lax",
    )
    return {"message": "Login successful"}

@router.post("/logout")
def logout(
    response: Response,
    session_id: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    if session_id:
        crud.delete_session_by_id(db, session_id=session_id)

    response.delete_cookie(key="session_id")
    return {"message": "Logout successful"}


# ✅ 회원가입: /users/
@router.post("/", response_model=schemas.User, summary="회원가입")
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)


@router.get("/me/topic-stats", response_model=list[schemas.UserTopicStatResponse])
def get_my_topic_stats(
    db: Session = Depends(get_db),
    me = Depends(get_current_user),
):
    stats = crud.list_user_topic_stats(db, me.id)

    res = []
    for s in stats:
        wrong_rate = (s.wrong_count / s.attempt_count) if s.attempt_count else 0.0
        res.append(schemas.UserTopicStatResponse(
            topic=s.topic,
            attempt_count=s.attempt_count,
            correct_count=s.correct_count,
            wrong_count=s.wrong_count,
            wrong_rate=wrong_rate,
            last_attempt_at=s.last_attempt_at,
        ))
    return res

# ✅ 특정 사용자 조회: /users/{user_id}
@router.get("/{user_id}", response_model=schemas.User, summary="특정 사용자 정보 확인")
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user