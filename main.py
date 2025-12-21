from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# [DB 관련]
from database import engine
from users import models

# [Redis 관련]
from services.cover_letter.cache import init_redis, close_redis

# [라우터 임포트 - 팀원들 것]
from routers.github_interview_router import router as github_interview_router
from routers.cs_interview_router import router as cs_interview_router
from users.userApi import router as users_router

# [라우터 임포트 - 내 것 (방금 만든 파일들)]
from routers.news_career_router import router as news_career_router
from routers.cover_letter_router import router as cover_letter_router

load_dotenv()

# DB 초기화
models.Base.metadata.create_all(bind=engine)

# ======================================================
# Lifespan: 앱 시작/종료 시 실행될 로직 (Redis 관리)
# ======================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Server Starting... Connecting to Redis...")
    await init_redis()  # Redis 연결
    yield
    print("👋 Server Shutting down... Closing Redis...")
    await close_redis() # Redis 연결 해제

# ======================================================
# 앱 설정 (FastAPI 선언은 여기서 딱 한 번만!)
# ======================================================
app = FastAPI(
    title="IT Interview & Career Service",
    description="CS 면접, 자소서 생성, 뉴스 트렌드 분석 통합 API",
    version="0.3.0",
    lifespan=lifespan # ★ 중요: Redis lifespan 등록
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================================
# 라우터 조립 (팀원 + 내 코드)
# ======================================================
app.include_router(github_interview_router)
app.include_router(cs_interview_router)
app.include_router(users_router)

# 내 라우터 추가
app.include_router(news_career_router)
app.include_router(cover_letter_router)

@app.get("/")
def read_root():
    return {"message": "All Systems Operational (Redis, DB, RAG)"}