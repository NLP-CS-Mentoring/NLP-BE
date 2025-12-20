from pathlib import Path
from .chroma_client import get_collection

BASE_DIR = Path(__file__).resolve().parent
QUESTION_DIR = BASE_DIR / "csQuestion"

collection = get_collection()


def parse_qna_file(path: Path):
    """
    파일 전체를 읽어서 (질문, 채점용 핵심정답, 전체 정답) 튜플로 반환.

    형식 1 (추천):
        질문문장|||정답 시작
        정답 계속...
        정답 계속...

    형식 2 (백업):
        질문만 있는 첫 줄
        정답...
        정답...
    """
    text = path.read_text(encoding="utf-8")

    if "|||" in text:
        q, a = text.split("|||", 1)
        question = q.strip()
        full_answer = a.strip()
    else:
        lines = text.splitlines()
        if not lines:
            return None, None, None
        question = lines[0].strip()
        full_answer = "\n".join(lines[1:]).strip()

    if not question:
        return None, None, None

    # ✅ 채점용 핵심 정답 = 첫 문단(빈 줄 기준)
    paragraphs = [p.strip() for p in full_answer.split("\n\n") if p.strip()]
    core_answer = paragraphs[0] if paragraphs else full_answer

    return question, core_answer, full_answer


def classify_topic(question: str) -> str:
    q = question.lower()

    if any(k in q for k in ["객체 지향", "oop", "클래스", "상속", "다형성"]):
        return "OOP / Design"
    if any(k in q for k in ["process", "thread", "deadlock", "프로세스", "스레드", "교착"]):
        return "Operating System"
    if any(k in q for k in ["tcp", "udp", "http", "https", "3-way", "dns", "네트워크"]):
        return "Network"
    if any(k in q for k in ["index", "transaction", "정규화", "트랜잭션", "데이터베이스", "db"]):
        return "Database"
    if any(k in q for k in ["시간 복잡도", "big-o", "stack", "queue", "tree", "graph", "bfs", "dfs"]):
        return "Data Structure / Algorithm"
    if any(k in q for k in ["프론트엔드", "react", "브라우저", "dom", "렌더링", "javascript", "자바스크립트"]):
        return "Frontend"

    return "General CS"


def main():
    if not QUESTION_DIR.exists():
        print(f"{QUESTION_DIR} 디렉토리가 없습니다. 경로를 확인하세요.")
        return

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []

    for path in QUESTION_DIR.rglob("*.txt"):
        filename = path.name

        question, core_answer, full_answer = parse_qna_file(path)
        if not question:
            print(f"⚠ {filename} 에서 질문을 파싱하지 못했습니다. 건너뜀.")
            continue

        topic = classify_topic(question)
        doc_id = filename   # B 방식: 파일 하나 = 문제 하나

        ids.append(doc_id)
        documents.append(question)
        metadatas.append(
            {
                "file": filename,
                "topic": topic,
                "answer_core": core_answer,   # 채점용 짧은 답
                "answer_full": full_answer,   # 텍스트 파일 전체 내용
            }
        )

    if not documents:
        print("등록할 질문이 없습니다. csQuestion 폴더를 확인하세요.")
        return

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    print(f"✨ 총 {len(documents)}개의 문제를 Chroma에 저장했습니다.")


if __name__ == "__main__":
    main()