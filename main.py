import os  
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# [DB 관련]
from database import engine
from users import models

# [Redis 관련]
from services.cover_letter.cache import init_redis, close_redis
from services.Algorithm.hint_bot import ensure_collection  
# [ROuter 임포트]
from routers.github_interview_router import router as github_interview_router
from routers.cs_interview_router import router as cs_interview_router
from users.userApi import router as users_router
from routers.algorithm_router import router as algorithm_router
from routers.news_career_router import router as news_career_router
from routers.cover_letter_router import router as cover_letter_router
from routers.agent_router import router as agent_router

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
    try:
        ensure_collection()
        print("✅ Chroma collection ready.")
    except Exception as e:
        print(f"⚠️ Chroma init failed: {e}")
    yield
    print("👋 Server Shutting down... Closing Redis...")
    await close_redis() # Redis 연결 해제

# ======================================================
# 앱 설정
# ======================================================
app = FastAPI(
    title="IT Interview & Career Service",
    description="CS 면접, 자소서 생성, 뉴스 트렌드 분석 통합 API",
    version="0.4.0",
    lifespan=lifespan
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
# 정적 파일(PDF) 다운로드 경로 설정
# ======================================================
# 1. main.py 위치 기준으로 'outputs' 폴더 경로 찾기
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

# 2. 폴더가 없으면 에러 나니까 미리 생성 (안전장치)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 3. 브라우저가 '/downloads'로 접속하면 'outputs' 폴더를 보여주도록 연결(Mount)
app.mount("/downloads", StaticFiles(directory=OUTPUT_DIR), name="downloads")


# ======================================================
# 라우터 조립
# ======================================================
app.include_router(github_interview_router)
app.include_router(cs_interview_router)
app.include_router(users_router)
app.include_router(news_career_router)
app.include_router(cover_letter_router)
app.include_router(agent_router)
app.include_router(algorithm_router)

@app.get("/")
def read_root():
    return {"message": "All Systems Operational (Redis, DB, RAG, File Server)"}