# users/schemas.py  (Pydantic v1 호환)
from typing import List, Optional
import datetime
from pydantic import BaseModel


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserTopicStat(BaseModel):
    topic: str
    attempt_count: int
    correct_count: int
    wrong_count: int
    last_attempt_at: Optional[datetime.datetime] = None
    updated_at: datetime.datetime

    class Config:
        orm_mode = True


class UserTopicStatResponse(BaseModel):
    topic: str
    attempt_count: int
    correct_count: int
    wrong_count: int
    wrong_rate: float
    last_attempt_at: Optional[datetime.datetime] = None

    class Config:
        orm_mode = True


class User(UserBase):
    id: int
    created_at: datetime.datetime

    # SQLAlchemy User.topic_stats 관계가 있으니까 맞춰두면 직렬화 안정적
    topic_stats: List[UserTopicStat] = []

    class Config:
        orm_mode = True