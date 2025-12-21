import os
import json
from typing import List
from dotenv import load_dotenv

# 랭체인 관련
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# 환경변수 로드
load_dotenv()

# [설정] create_db.py와 경로가 같아야 함
DB_PATH = "./news_chroma_db"
COLLECTION_NAME = "it_news_data"

# [출력 데이터 구조 정의]
class TrendReportStructure(BaseModel):
    summary: List[str] = Field(description="최신 기술 뉴스 3줄 요약 리스트 (구체적 기술명 포함)")
    keywords: List[str] = Field(description="핵심 기술 키워드 5개 리스트")
    atmosphere_status: str = Field(description="개발자 생태계 분위기 ('긍정', '부정', '보통' 중 하나)")
    atmosphere_percent: str = Field(description="긍정 또는 부정일 경우 몇 퍼센트인지")
    atmosphere_reason: str = Field(description="분위기에 대한 이유 한 문장")

def get_vector_store():
    """저장된 DB 로드"""
    if not os.path.exists(DB_PATH):
        print("❌ DB가 없습니다. 'create_db.py'를 먼저 실행하세요.")
        return None

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return Chroma(
        persist_directory=DB_PATH,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME
    )

def analyze_trends():
    """트렌드 분석 리포트 생성"""
    vectorstore = get_vector_store()
    if not vectorstore: return

    print("\n🧠 [트렌드 분석] 최신 뉴스 분석 중...")
    
    # [수정 전]
    # retriever = vector_store.as_retriever(search_kwargs={"k": 8})

    # [수정 후] ★ MMR 방식 적용
    retriever = vectorstore.as_retriever(
        search_type="mmr",  # 다양성 기반 검색 활성화
        search_kwargs={
            "k": 8,          # 최종적으로 가져올 문서 개수
            "fetch_k": 30,   # 다양성을 확보하기 위해 처음에 후보로 훑어볼 문서 개수 (넓게 보고 추림)
            "lambda_mult": 0.6  # 0.0(완전 다양성) ~ 1.0(완전 정확도). 0.5~0.7 추천
        }
    )
    query = "개발자 취업, 최신 AI 모델"
    retrieved_docs = retriever.invoke(query)
    
    # 2. LLM 체인 실행
    parser = JsonOutputParser(pydantic_object=TrendReportStructure)
    
    template = """
    너는 시니어 테크 리드야. 아래 뉴스들을 분석해서 개발자들을 위한 트렌드 리포트를 작성해.
    
    [중요 지침]
    1. 특정 기업(예: Meta, Google) 하나의 소식만 편중되지 않게 해.
    2. 검색된 뉴스에 다양한 기업이나 기술이 있다면 골고루 포함해서 요약해.
    3. 핵심 기술 키워드 같은 경우는 조사를 빼고 명사 형태의 핵심 키워드만 찾아.
    4. 핵심 키워드에는 코딩, 오픈소스 같은거 말고 새롭게 나온 모델 이름이나 기술 이름 같은걸 말해줘.
    5. 개발자 생태계 분위기 같은 경우, AI가 아닌 개발자의 입장에서 기업에 취업하는게 쉬운지 어려운지에 따라 긍정과 부정으로 구분해줘. 그리고 긍정과 부정 몇 퍼센트인지도 알려줘.
    
    [분석 대상 뉴스]
    {context}

    [출력 형식]
    {format_instructions}
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    chain = prompt | llm | parser
    
    context_text = "\n\n".join([doc.page_content for doc in retrieved_docs])
    
    try:
        result = chain.invoke({
            "context": context_text,
            "format_instructions": parser.get_format_instructions()
        })
        return result
    except Exception as e:
        print(f"❌ 분석 실패: {e}")
        return None

def recommend_articles(user_interest, k=3):
    """사용자 맞춤 기사 추천"""
    vectorstore = get_vector_store()
    if not vectorstore: return []

    print(f"\n🔍 [기사 추천] 키워드: '{user_interest}'")
    results = vectorstore.similarity_search(user_interest, k=k)
    
    recs = []
    for doc in results:
        recs.append({
            "title": doc.metadata.get("title", "무제"),
            "link": doc.metadata.get("link", "#"),
            "preview": doc.page_content[:100] + "..."
        })
    return recs

if __name__ == "__main__":
    # 1. 트렌드 분석
    report = analyze_trends()
    if report:
        print(json.dumps(report, indent=2, ensure_ascii=False))

    # 2. 기사 추천 예시
    my_interest = "RAG 및 LLM 최적화"
    recommendations = recommend_articles(my_interest)
    
    for r in recommendations:
        print(f"- {r['title']} ({r['link']})")