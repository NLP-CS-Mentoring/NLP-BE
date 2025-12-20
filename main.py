# main.py
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from githubInterview.githubInterviewApi import router as github_interview_router  
from csInterview.csInterviewApi import router as cs_interview_router
from users.userApi import router as users_router

from database import engine
from users import models
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=engine)

from dotenv import load_dotenv
load_dotenv()

from csInterview.random_service import reload_questions

app = FastAPI(
    title="CS Interview Question Service",
    description="Chroma + txt 기반 CS 면접 문제 랜덤 제공 & 채점 API",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(github_interview_router)
app.include_router(cs_interview_router)
app.include_router(users_router)