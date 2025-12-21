import os
import json
import shutil
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from tqdm import tqdm

# 1. 환경 변수 로드 (API Key)
load_dotenv()

# ── [설정] ──
INPUT_FILE = "job_postings_final_qwen32b.json"  # 정제된 데이터 파일
DB_PATH = "./chroma_db"                 # 벡터 DB가 저장될 로컬 폴더 경로
COLLECTION_NAME = "job_postings"        # DB 내부의 컬렉션 이름

def create_vector_db():
    # 2. 데이터 파일 로드
    if not os.path.exists(INPUT_FILE):
        print(f"❌ '{INPUT_FILE}' 파일이 없습니다. 경로를 확인해주세요.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        jobs = json.load(f)
    
    print(f"📂 데이터 로드 완료: {len(jobs)}개 공고")

    # 3. 문서(Document) 객체로 변환
    # LangChain이 이해할 수 있는 형태로 변환합니다.
    documents = []
    
    print("🔄 데이터 가공 중...")
    for job in tqdm(jobs):
        # (1) 벡터화할 텍스트 (AI가 의미를 파악해야 할 핵심 내용)
        # 검색 정확도를 높이기 위해 회사명, 제목, 본문을 합칩니다.
        page_content = f"""
        [회사명] {job.get('company', '미상')}
        [공고명] {job.get('title', '제목 없음')}
        [상세 내용]
        {job.get('content', '')}
        """.strip()

        # (2) 메타데이터 (나중에 필터링하거나 출처 표기용)
        metadata = {
            "company": job.get('company', '미상'),
            "title": job.get('title', '제목 없음'),
            "link": job.get('link', ''),
            "pubDate": job.get('pubDate', '정보 없음')
        }

        doc = Document(page_content=page_content, metadata=metadata)
        documents.append(doc)

    # 4. 임베딩 모델 설정 (gpt-4o-mini와 궁합이 좋은 모델)
    # text-embedding-3-small: 가격이 저렴하고 성능이 우수함
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # 5. 기존 DB가 있다면 초기화 (선택 사항)
    # 깨끗하게 새로 만들고 싶다면 주석을 해제하세요.
    # if os.path.exists(DB_PATH):
    #     shutil.rmtree(DB_PATH)
    #     print(f"🗑️ 기존 DB({DB_PATH}) 삭제 완료")

    # 6. 벡터 DB 생성 및 저장 (Persistent)
    print(f"🚀 벡터 DB 생성 및 저장 시작... (경로: {DB_PATH})")
    
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=DB_PATH  # ★ 여기가 핵심: 로컬 폴더에 저장
    )

    print(f"🎉 벡터 DB 구축 완료! 총 {len(documents)}개의 문서가 저장되었습니다.")
    print(f"   저장 위치: {os.path.abspath(DB_PATH)}")

# ── [검증 테스트] ──
def test_vector_db():
    print("\n🔍 [검증 테스트] 저장된 DB에서 검색을 시도합니다...")
    
    # 저장된 DB 불러오기
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