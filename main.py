from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any # Dict, Any 추가 필요
import rag_core

app = FastAPI()

# --- 데이터 모델 정의 ---

# ★ 변경: report 필드가 문자열(str)이 아니라 객체(Dict)입니다.
class ReportResponse(BaseModel):
    article_count: int
    report: Dict[str, Any] 

class UserRequest(BaseModel):
    interest: str

class ArticleResponse(BaseModel):
    title: str
    link: str
    pubDate: str
    content: str 

# --- API 엔드포인트 ---

@app.get("/")
def read_root():
    return {"message": "IT 뉴스 RAG 서버가 정상 작동 중입니다."}

@app.get("/analyze", response_model=ReportResponse)
def get_trend_analysis():
    news_data = rag_core.load_and_filter_data("it_news_with_content.json")
    if not news_data:
        raise HTTPException(status_code=404, detail="데이터 파일이 없거나 비어있습니다.")

    docs = rag_core.create_documents(news_data)
    
    # rag_core가 이제 JSON 객체를 반환합니다.
    report, count = rag_core.analyze_trends(docs)

    return {
        "article_count": count,
        "report": report
    }

@app.post("/recommend", response_model=List[ArticleResponse])
def get_recommendations(user: UserRequest):
    news_data = rag_core.load_and_filter_data("it_news_with_content.json")
    if not news_data:
        raise HTTPException(status_code=404, detail="데이터 파일이 없거나 비어있습니다.")

    docs = rag_core.create_documents(news_data)
    results = rag_core.recommend_articles(docs, user.interest, k=5)
    
    return results