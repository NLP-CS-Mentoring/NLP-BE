from fastapi import APIRouter, HTTPException
from typing import List

import schemas
from services.news import analyze_news
from services.career import recommend_tech

router = APIRouter(
    tags=["RAG (News & Career)"]
)

@router.get("/news/analyze", response_model=schemas.NewsReportResponse)
def get_news_trend():
    report = analyze_news.analyze_trends()
    if not report:
        raise HTTPException(status_code=500, detail="뉴스 분석 실패")
    return {"report": report}

@router.post("/news/recommend", response_model=List[schemas.ArticleResponse])
def recommend_news(req: schemas.NewsRequest):
    results = analyze_news.recommend_articles(req.interest, k=5)
    formatted_results = []
    for r in results:
        formatted_results.append({
            "title": r.get("title", ""),
            "link": r.get("link", ""),
            "preview": r.get("preview", ""),
            "pubDate": r.get("pubDate", "")
        })
    return formatted_results

@router.post("/career/advice", response_model=schemas.CareerResponse)
def get_career_advice(req: schemas.CareerRequest):
    try:
        result_text = recommend_tech.get_career_advice(req.query)
        return {"advice": result_text}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))