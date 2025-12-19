from typing import List, Optional
import datetime
from pydantic import BaseModel, ConfigDict

class UserTopicStatResponse(BaseModel):
    topic: str
    attempt_count: int
    correct_count: int
    wrong_count: int
    wrong_rate: float
    last_attempt_at: Optional[datetime.datetime] = None

    model_config = ConfigDict(from_attributes=True)



class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class User(UserBase):
    id: int
    created_at: datetime.datetime
    topic_stats: List[UserTopicStatResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

        