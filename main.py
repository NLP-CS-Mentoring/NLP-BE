# main.py
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from githubInterview.githubInterviewApi import router as github_interview_router  
from csInterview.csInterviewApi import router as cs_interview_router

from dotenv import load_dotenv
load_dotenv()

from csInterview.random_service import reload_questions

app = FastAPI(
    title="CS Interview Question Service",
    description="Chroma + txt 기반 CS 면접 문제 랜덤 제공 & 채점 API",
    version="0.3.0",
)

app.include_router(github_interview_router)
app.include_router(cs_interview_router)
from users.api import router as users_router
from users import models as users_models

# init users DB
users_models.init_db()
app.include_router(users_router, prefix="/auth")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 나중에 프론트 도메인으로 좁혀도 됨
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    reload_questions()


# `csInterview` 엔드포인트들은 `csInterview.api` 라우터로 이동했습니다.