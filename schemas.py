from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# ==========================================
# 📰 뉴스 관련 모델 (News)
# ==========================================

# 뉴스 트렌드 분석 결과 (analyze_trends의 결과물)
# `NewsReportResponse`가 BaseModel의 상속을 받도록 만든것, 이 BaseModel을 적은 이유는 이 클래스는 Pydnantic의 데이터 검증 기능을 사용하겠다고 선언
class NewsReportResponse(BaseModel):
    report: Dict[str, Any]  # 딕셔너리의 Key는 무조건 "문자열"이어야 한다. Value는 무엇이든 올 수 있다는 뜻이다.

# 뉴스 추천 요청 (사용자가 보낼 데이터)
class NewsRequest(BaseModel):
    interest: str

# 뉴스 추천 응답 (사용자에게 줄 데이터)
class ArticleResponse(BaseModel):
    title: str
    link: str
    preview: str
    pubDate: Optional[str] = None

# ==========================================
# 💼 채용/커리어 관련 모델 (Career)
# ==========================================

# 커리어 조언 요청
class CareerRequest(BaseModel):
    query: str  # 예: "백엔드 신입 취업 로드맵 알려줘"

# 커리어 조언 응답
class CareerResponse(BaseModel):
    advice: str # LLM의 답변 텍스트