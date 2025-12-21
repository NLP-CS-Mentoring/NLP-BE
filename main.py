# ------------------------------- 인 메모리 사용(v1) --------------------------------------
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from cover_letter.loader import load_text_from_file
from cover_letter.analyzer import analyze_style
from cover_letter.generator import generate_cover_letter

import hashlib
import time

load_dotenv()
# uv run python -m uvicorn main:app
# 파일 받고 스타일 분석하는 부분을 캐시를 사용해서 응답 속도 늘리기 위함(약 53%정도 속도 개선)
# 파일 캐시 저장소 -> redis로 변경 main_redis.py 참조
CACHE = {}
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# main.py
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from typing import List

# ★ 만든 모듈들 임포트
import schemas         # 데이터 모델 (schemas.py)
import analyze_news    # 뉴스 분석 엔진
import recommend_tech  # 채용 분석 엔진

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

class BasicRequest(BaseModel):
    user_fact: str # 사용자 입력

# 1. 기본 자소서 생성 API (파일 X)
@app.post("/generate/basic")
def generate_basic_letter(req: BasicRequest):
    """
    파일 없이 사용자의 경험만 받아 표준 스타일로 자소서를 생성
    """
    if not req.user_fact:
        raise HTTPException(status_code=400, detail="user_fact is empty")

    try:
        result = generate_cover_letter(user_fact=req.user_fact, style_guide=None)
        
        return {
            "status": "success",
            "mode": "basic",
            "result": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. 스타일 기반 자소서 생성 API (파일 O)
@app.post("/generate/with-style")
async def generate_styled_cover_letter(
    file: UploadFile = File(...),
    user_fact: str = Form(...)
):
    """
    파일을 포함해 PDF나 TXT 파일을 업로드받아 말투를 분석한 후, 그 스타일로 자소서를 생성
    """

    t0 = time.time()

    if not (file.filename.endswith('.pdf') or file.filename.endswith('.txt')):
        raise HTTPException(status_code=400, detail="PDF 또는 TXT 파일만 등록가능합니다.")

    try:
        # [Phase 1]
        content = await file.read()
        file_hash = hashlib.sha256(content).hexdigest()

        t1 = time.time()
        phase_1 = t1 - t0

        # [Phase 2]
        if file_hash in CACHE: # 캐시 히트
            style_result = CACHE[file_hash]

            t2 = time.time()
            phase_2 = t2 - t1
        else: # 캐시 미스
            raw_text = load_text_from_file(content, file.filename) # pdf나 txt로 부터 텍스트 읽어오기
            style_result = analyze_style(raw_text) # 스타일 분석
            CACHE[file_hash] = style_result

            t2 = time.time()
            phase_2 = t2 - t1
        
        # [Phase 3]
        final_result = generate_cover_letter(user_fact=user_fact, style_guide=style_result) # 자소서 생성

        t3 = time.time()
        phase_3 = t3 - t2
        total_time = t3 - t0

        print(f"total_time: {round(total_time, 4)}, phase_1: {round(phase_1, 4)}, phase_2: {round(phase_2, 4)}, phase_3: {round(phase_3, 4)}")
        # total_time(캐시 미스): 10.9809, phase_1: 0.0022, phase_2: 4.7772, phase_3: 6.2015
        # total_time(캐시 히트): 7.13, phase_1: 0.0021, phase_2: 0.0, phase_3: 7.1279

        return {
            "status": "success",
            "mode": "style_transfer",
            "analyzed_style": style_result,
            "result": final_result,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(github_interview_router)
app.include_router(cs_interview_router)
app.include_router(users_router)
# --- [API 엔드포인트] ---

@app.get("/")
def read_root():
    return {"message": "IT 커리어 & 뉴스 통합 RAG 서버입니다."}

# === [기능 A] 뉴스 분석 및 추천 ===

@app.get("/news/analyze", response_model=schemas.NewsReportResponse)
def get_news_trend():
    """뉴스 트렌드 리포트 생성"""
    report = analyze_news.analyze_trends()
    
    if not report:
        raise HTTPException(status_code=500, detail="뉴스 분석 실패 (DB 확인 필요)")
    
    return {"report": report}

@app.post("/news/recommend", response_model=List[schemas.ArticleResponse])
def recommend_news(req: schemas.NewsRequest):
    """뉴스 기사 추천"""
    results = analyze_news.recommend_articles(req.interest, k=5)
    
    # schemas.ArticleResponse 형태에 맞춰 변환
    formatted_results = []
    for r in results:
        formatted_results.append({
            "title": r.get("title", ""),
            "link": r.get("link", ""),
            "preview": r.get("preview", ""),
            "pubDate": r.get("pubDate", "")
        })
    return formatted_results

# === [기능 B] 채용 공고 기반 커리어 컨설팅 ===

@app.post("/career/advice", response_model=schemas.CareerResponse)
def get_career_advice(req: schemas.CareerRequest):
    """채용 공고 데이터 기반 커리어 조언"""
    print(f"🤔 커리어 상담 요청: {req.query}")
    
    try:
        # recommend_tech 모듈 호출
        result_text = recommend_tech.get_career_advice(req.query)
        return {"advice": result_text}
    except Exception as e:
        print(f"에러 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 서버 실행: uvicorn main:app --reload
