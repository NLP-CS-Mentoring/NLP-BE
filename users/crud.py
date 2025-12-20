# users/crud.py
import datetime
import secrets
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc

from . import models, schemas
from .security import get_password_hash


# =========================
# User
# =========================
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# =========================
# Session
# =========================
def create_user_session(db: Session, user_id: int) -> models.UserSession:
    session_id = secrets.token_hex(32)

    # ✅ UTC-aware
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    expires_at = now_utc + datetime.timedelta(days=7)

    db_session = models.UserSession(
        session_id=session_id,
        user_id=user_id,
        expires_at=expires_at,
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def get_user_by_session_id(db: Session, session_id: str) -> models.User | None:
    now_utc = datetime.datetime.now(datetime.timezone.utc)

    session = db.query(models.UserSession).filter(
        models.UserSession.session_id == session_id,
        models.UserSession.expires_at > now_utc,
    ).first()

    return session.user if session else None


def delete_session_by_id(db: Session, session_id: str):
    session = db.query(models.UserSession).filter(models.UserSession.session_id == session_id).first()
    if session:
        db.delete(session)
        db.commit()


# =========================
# Topic stats
# =========================
def list_user_topic_stats(db: Session, user_id: int):
    return (
        db.query(models.UserTopicStat)
        .filter(models.UserTopicStat.user_id == user_id)
        .order_by(desc(models.UserTopicStat.updated_at))
        .all()
    )

def update_user_topic_stats(
    db: Session,
    *,
    user_id: int,
    topic: str,
    is_correct: bool,
):
    now = datetime.datetime.now()

    stat = (
        db.query(models.UserTopicStat)
        .filter(
            models.UserTopicStat.user_id == user_id,
            models.UserTopicStat.topic == topic,
        )
        .first()
    )

    if stat is None:
        stat = models.UserTopicStat(
            user_id=user_id,
            topic=topic,
            attempt_count=0,
            correct_count=0,
            wrong_count=0,
            last_attempt_at=None,
        )
        db.add(stat)

        # 동시성 대비
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            stat = (
                db.query(models.UserTopicStat)
                .filter(
                    models.UserTopicStat.user_id == user_id,
                    models.UserTopicStat.topic == topic,
                )
                .first()
            )
            if stat is None:
                raise

    stat.attempt_count += 1
    if is_correct:
        stat.correct_count += 1
    else:
        stat.wrong_count += 1

    stat.last_attempt_at = now

    db.commit()
    db.refresh(stat)
    return stat