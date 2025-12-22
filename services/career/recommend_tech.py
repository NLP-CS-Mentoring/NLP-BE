import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# 1. 설정
load_dotenv()
DB_PATH = "./jobKorea_chroma_db"          
COLLECTION_NAME = "job_postings" 

# 2. 로컬 벡터 DB 및 체인 초기화 함수
def get_rag_chain():
    """
    DB와 체인을 초기화하여 반환합니다. 
    (모듈 임포트 시점에 실행되지 않고, 필요할 때 로드하거나 전역으로 둬도 됨)
    """
    if not os.path.exists(DB_PATH):
        print(f"❌ 오류: {DB_PATH} 경로에 채용 공고 DB가 없습니다.")
        return None

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # DB 로드
    vector_store = Chroma(
        persist_directory=DB_PATH,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME
    )
    
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    template = """
    당신은 IT 취업 컨설턴트입니다.
    사용자가 희망하는 직무에 대해, 실제 채용 공고 데이터를 기반으로 분석하고 조언해줘야 합니다.

    [참고할 채용 공고들]
    {context}

    [사용자 질문]
    {question}

    [답변 가이드]
    1. **[핵심 기술 분석]**
       - 검색된 공고들을 종합하여, 해당 직무에서 가장 많이 요구하는 기술 스택 3가지를 선정하고 이유를 설명하세요.

    2. **[단계별 학습 로드맵]**
       - 취업을 위해 어떤 순서로 공부하면 좋을지 구체적인 로드맵을 제안하세요.

    3. **[참고한 기업별 상세 정보] (중요)**
       - 검색된 기업들의 채용 정보를 아래 형식에 맞춰 빠짐없이 정리해주세요.
       - 자격 요건과 우대 사항은 핵심만 요약해서 보여주세요.

       [형식 예시]
       - **기업명**: [공고 보러가기](URL링크)
         - **자격 요건**: ...
         - **우대 사항**: ...
    """
    
    prompt = ChatPromptTemplate.from_template(template)

    def format_docs(docs):
        formatted_list = []
        for d in docs:
            company = d.metadata.get('company', '미상')
            link = d.metadata.get('link', '#') 
            content = d.page_content
            formatted_text = f"[기업명: {company}]\n[URL: {link}]\n{content}"
            formatted_list.append(formatted_text)
        return "\n\n".join(formatted_list)

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return chain

# 만약 DB가 없을 경우 예외 처리
try:
    career_chain = get_rag_chain()
except Exception as e:
    print(f"⚠️ 채용 공고 RAG 초기화 실패: {e}")
    career_chain = None

def get_career_advice(query: str):
    if not career_chain:
        return "죄송합니다. 채용 공고 데이터베이스가 준비되지 않았습니다."
    
    return career_chain.invoke(query)

if __name__ == "__main__":
    # 테스트용 코드
    print(get_career_advice("AI 에이전트 개발자"))