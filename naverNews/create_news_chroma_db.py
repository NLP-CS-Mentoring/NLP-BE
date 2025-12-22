import json
import os
import shutil
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

load_dotenv()

NEWS_JSON_PATH = "it_news_with_content.json" 
DB_PATH = "./news_chroma_db"                 
COLLECTION_NAME = "it_news_data"

def is_tech_news(news_item):
    """뉴스 필터링 로직: 주식/금융 기사 제외, 기술 키워드 포함 여부 확인"""
    title = news_item.get('title', '')
    content = news_item.get('content', '')
    text = title + " " + content
    
    stop_words = ["코스닥", "코스피", "상장", "주가", "매수", "목표가", "금융위", "영업이익", "매출", "전년비", "배당", "ETF", "증권", "금리"]
    tech_keywords = ["모델", "공개", "출시", "개발", "기능", "플랫폼", "오픈소스", "API", "LLM", "GPT", "클라우드", "서버", "알고리즘", "업데이트", "베타", "AI", "러닝", "딥러닝", "프로그래밍", "언어", "프레임워크", "SW"]
    
    for word in stop_words:
        if word in title: return False
    return any(k in text for k in tech_keywords)

def build_vector_db():
    if not os.path.exists(NEWS_JSON_PATH):
        print(f"❌ '{NEWS_JSON_PATH}' 파일이 없습니다.")
        return

    with open(NEWS_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    documents = []
    for d in data:
        if len(d.get('content', '')) > 50 and is_tech_news(d):
            doc = Document(
                page_content=d['content'],
                metadata={
                    "title": d.get('title', ''),
                    "link": d.get('link', ''),
                    "pubDate": d.get('pubDate', '')
                }
            )
            documents.append(doc)
    
    if not documents:
        print("❌ 저장할 유효한 뉴스 데이터가 없습니다.")
        return

    print(f"📄 총 {len(documents)}개의 기사를 벡터화합니다.")

    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH)
        print(f"🗑️ 기존 DB 폴더({DB_PATH}) 삭제 완료")

    print(f"🚀 벡터 DB 생성 중... (경로: {DB_PATH})")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=DB_PATH
    )
    print("🎉 벡터 DB 구축 완료!")

if __name__ == "__main__":
    build_vector_db()