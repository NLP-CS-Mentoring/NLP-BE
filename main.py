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
