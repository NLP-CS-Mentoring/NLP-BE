import os
import json
import shutil
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from tqdm import tqdm

load_dotenv()


INPUT_FILE = "job_postings_final_qwen32b.json"
DB_PATH = "./chroma_db"                
COLLECTION_NAME = "job_postings"     

def create_vector_db():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ '{INPUT_FILE}' 파일이 없습니다. 경로를 확인해주세요.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        jobs = json.load(f)
    
    print(f"📂 데이터 로드 완료: {len(jobs)}개 공고")

  
    documents = []
    
    print("🔄 데이터 가공 중...")
    for job in tqdm(jobs):
        page_content = f"""
        [회사명] {job.get('company', '미상')}
        [공고명] {job.get('title', '제목 없음')}
        [상세 내용]
        {job.get('content', '')}
        """.strip()

        metadata = {
            "company": job.get('company', '미상'),
            "title": job.get('title', '제목 없음'),
            "link": job.get('link', ''),
            "pubDate": job.get('pubDate', '정보 없음')
        }

        doc = Document(page_content=page_content, metadata=metadata)
        documents.append(doc)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    print(f"🚀 벡터 DB 생성 및 저장 시작... (경로: {DB_PATH})")
    
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=DB_PATH 
    )

    print(f"🎉 벡터 DB 구축 완료! 총 {len(documents)}개의 문서가 저장되었습니다.")
    print(f"   저장 위치: {os.path.abspath(DB_PATH)}")


def test_vector_db():
    print("\n🔍 [검증 테스트] 저장된 DB에서 검색을 시도합니다...")
    
    
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    loaded_db = Chroma(
        persist_directory=DB_PATH, 
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME
    )

    query = "AI 에이전트 개발자"
    results = loaded_db.similarity_search(query, k=3)

    print(f"질문: '{query}'")
    for i, res in enumerate(results):
        print(f"[{i+1}] {res.metadata['company']} - {res.metadata['title']}")

if __name__ == "__main__":
    create_vector_db()
    test_vector_db()