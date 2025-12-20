import json
import os
from dotenv import load_dotenv
from typing import List

# 랭체인 및 Pydantic 관련 라이브러리
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
# ★ 변경 1: JsonOutputParser와 Pydantic 모델 가져오기
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# 환경변수 로드
load_dotenv()

# --- [0] 데이터 구조 정의 (LLM에게 강제할 JSON 형식) ---
class TrendReportStructure(BaseModel):
    summary: List[str] = Field(description="기술 뉴스 3줄 요약 리스트 (구체적 기술명 포함)")
    keywords: List[str] = Field(description="핵심 기술 키워드 5개 리스트")
    atmosphere_status: str = Field(description="개발자 취업 시장 및 생태계 분위기 ('긍정', '부정', '보통' 중 하나)")
    atmosphere_reason: str = Field(description="분위기에 대한 이유 한 문장")

# --- [1] 데이터 로드 및 필터링 ---
def is_tech_news(news_item):
    title = news_item.get('title', '')
    content = news_item.get('content', '')
    text = title + " " + content
    
    stop_words = [
        "코스닥", "코스피", "상장", "주가", "매수", "목표가", "금융위", 
        "영업이익", "매출", "전년비", "배당", "ETF", "증권", "금리"
    ]
    
    tech_keywords = [
        "모델", "공개", "출시", "개발", "기능", "플랫폼", "오픈소스", 
        "API", "LLM", "GPT", "클라우드", "서버", "알고리즘", "업데이트", "베타",
        "AI", "러닝", "딥러닝", "프로그래밍", "언어", "프레임워크"
    ]
    
    for word in stop_words:
        if word in title:
            return False

    has_tech_keyword = any(k in text for k in tech_keywords)
    return has_tech_keyword

def load_and_filter_data(file_path="it_news_with_content.json"):
    if not os.path.exists(file_path):
        print(f"❌ 오류: {file_path} 파일을 찾을 수 없습니다.")
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 데이터 로드 중 오류 발생: {e}")
        return []

    valid_data = []
    for d in data:
        if len(d.get('content', '')) > 50 and is_tech_news(d):
            valid_data.append(d)
            
    print(f"🧹 데이터 로드 완료: {len(valid_data)}개 기사 준비됨")
    return valid_data

def create_documents(news_data):
    documents = []
    for news in news_data:
        doc = Document(
            page_content=news['content'],
            metadata={
                "title": news['title'],
                "link": news['link'],
                "pubDate": news['pubDate']
            }
        )
        documents.append(doc)
    return documents

# --- [2] 전체 트렌드 분석 기능 (JSON 출력 수정됨) ---
def analyze_trends(documents):
    if not documents:
        # 데이터가 없을 때 빈 JSON 구조 반환
        return {
            "summary": [],
            "keywords": [],
            "atmosphere_status": "데이터 없음",
            "atmosphere_reason": "분석할 뉴스가 없습니다."
        }, 0

    print("🧠 [트렌드 분석] Vector DB 생성 중...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name="trend_analysis"
    )
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": 8})
    
    print("🔍 트렌드 키워드로 기사 검색 중...")
    retrieved_docs = retriever.invoke("새로운 AI 모델, 프로그래밍 언어, 개발 도구 업데이트, 오픈소스, 기술 트렌드")
    
    # ★ 변경 2: JSON 파서 설정
    parser = JsonOutputParser(pydantic_object=TrendReportStructure)

    # ★ 변경 3: 프롬프트에 포맷 지시사항(format_instructions) 추가
    template = """
    너는 개발자들을 위한 '시니어 테크 리드'야.
    아래 뉴스들을 바탕으로 **엔지니어 관점**의 기술 트렌드 리포트를 작성해.

    [금지 사항]
    - 주식, 투자, 금융 이야기는 절대 하지 마.
    - 마크다운 태그(```json) 없이 순수한 JSON만 출력해.

    [분석 대상 뉴스]
    {context}

    [출력 요구사항]
    반드시 아래 형식을 지켜서 JSON으로 답변해:
    {format_instructions}
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    
    # 체인 연결 (Prompt -> LLM -> JSON Parser)
    chain = prompt | llm | parser
    
    context_text = "\n\n".join([doc.page_content for doc in retrieved_docs])
    
    # 실행 및 파싱
    try:
        report_json = chain.invoke({
            "context": context_text,
            "format_instructions": parser.get_format_instructions()
        })
    except Exception as e:
        print(f"❌ 분석 생성 중 오류: {e}")
        report_json = {"error": "분석 실패"}

    vectorstore.delete_collection()
    
    return report_json, len(documents)

# --- [3] 사용자 맞춤형 추천 기능 ---
def recommend_articles(documents, user_interest, k=5):
    """
    사용자의 관심사(user_interest)와 가장 유사한 기사를 k개 찾아서 반환 (본문 포함)
    """
    if not documents:
        return []

    print(f"🔍 [맞춤 추천] 사용자 관심사: '{user_interest}' 분석 중...")
    
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name="recommendation_engine"
    )
    
    results = vectorstore.similarity_search(user_interest, k=k)
    
    recommendations = []
    for doc in results:
        recommendations.append({
            "title": doc.metadata.get("title", "제목 없음"),
            "link": doc.metadata.get("link", ""),
            "pubDate": doc.metadata.get("pubDate", ""),
            "content": doc.page_content, # 본문 전체 반환
        })
    
    vectorstore.delete_collection()
    
    return recommendations