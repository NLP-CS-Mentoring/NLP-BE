# users/models.py
import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)

    auth_sessions = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    topic_stats = relationship(
        "UserTopicStat",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserSession(Base):
    __tablename__ = "user_sessions"

    session_id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="auth_sessions")


class UserTopicStat(Base):
    __tablename__ = "user_topic_stats"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    topic = Column(String, nullable=False, index=True)

    attempt_count = Column(Integer, default=0, nullable=False)
    correct_count = Column(Integer, default=0, nullable=False)
    wrong_count = Column(Integer, default=0, nullable=False)

    last_attempt_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, nullable=False)

    user = relationship("User", back_populates="topic_stats")

    __table_args__ = (
        UniqueConstraint("user_id", "topic", name="uq_user_topic"),
    )