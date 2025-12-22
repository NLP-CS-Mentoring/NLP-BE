# 🚀 AI-Powered Tech Career Platform Backend

> **"개발자 취업의 A to Z: 면접부터 자소서, 트렌드 분석까지"** > AI Agent, RAG, OCR 등 최신 기술을 활용하여 취업 준비 과정을 자동화하고 개인화된 솔루션을 제공하는 백엔드 서비스입니다.

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-RAG-1C3C3C?logo=langchain&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?logo=openai&logoColor=white)
![ChromaDB](https://img.shields.io/badge/VectorDB-Chroma-purple)

---

## 📖 프로젝트 개요 (Overview)

이 프로젝트는 취업 준비생이 겪는 정보의 홍수와 반복적인 작업 부담을 줄이기 위해 개발되었습니다.  
단순한 챗봇을 넘어 **실제 행동(Action)을 수행하는 AI Agent**를 탑재하였으며, **Vector DB**를 통해 노이즈가 제거된 고품질의 IT 정보만을 제공합니다. 또한, 이미지로 된 채용 공고까지 분석하는 **OCR 기술**을 도입하여 데이터의 사각지대를 없앴습니다.

---

## 🌟 핵심 기능 (Key Features)

### 1️⃣ 🧠 AI 면접 코치 (Smart Interview Prep)
- **CS 지식 면접**: 운영체제, 네트워크, 자료구조 등 핵심 CS 주제에 대한 꼬리에 꼬리를 무는 질문 및 피드백.
- **GitHub 기반 면접**: 사용자의 GitHub 레포지토리를 분석하여, 실제 작성한 프로젝트 코드에 기반한 맞춤형 예상 질문 생성.

### 2️⃣ 📝 AI 자소서 & Action Agent (Cover Letter & Automation)
- **페르소나 기반 작성**: 사용자의 경험과 평소 말투를 학습하여 '나다운' 자소서 초안 생성.
- **Action Agent**:
  - 자소서 작성 중 궁금한 CS 지식 실시간 답변.
  - **PDF 자동 생성**: 완성된 자소서를 명령어 한 번으로 PDF 변환 및 다운로드 (한글 줄바꿈 최적화 적용).
  - **이메일 전송**: 생성된 파일을 지정된 이메일로 즉시 발송.

### 3️⃣ 🧩 알고리즘 헬퍼 (Algorithm Helper)
- **문제 분석 및 힌트**: 문제 지문을 입력하면 AI가 알고리즘 유형(DP, DFS 등)을 분석하고 풀이 접근법(Hint) 제공.
- **유사 문제 추천**: 현재 문제와 논리가 유사한 기출 문제를 추천하여 심화 학습 유도.

### 4️⃣ 📰 IT 트렌드 분석 & 큐레이션 (Tech Trends RAG)
- **업계 분위기 리포트**: 최신 IT 뉴스를 크롤링/요약하여 **"긍정/부정 여론(%)"** 및 **"핵심 키워드"** 시각화.
- **정제된 뉴스 추천 (Vector DB)**: 
  - 일반 포털 검색과 달리, **Vector DB**를 구축하여 AI 관련 주가/경제/가십 기사는 필터링.
  - 오직 **기술적 가치가 있는 기사**만을 임베딩하여 사용자 관심 분야(예: LLM, MSA)에 맞춰 추천.

### 5️⃣ 🗺️ 채용 공고 기반 로드맵 (Job Roadmap & OCR)
- **OCR 공고 분석**: 텍스트 없이 통이미지로 된 '불친절한' 채용 공고도 **Tesseract OCR**로 텍스트화하여 분석.
- **실전 학습 로드맵**: 희망 직무의 실제 공고 데이터를 종합하여, **"어떤 기술 스택을 먼저 공부해야 하는지"** 우선순위 로드맵 제시.
- **근거 데이터 제공**: 로드맵의 근거가 된 실제 기업의 자격 요건, 우대 사항, 공고 링크를 함께 제공하여 신뢰성 확보.

---

## 🛠️ 기술 스택 (Tech Stack)

| 구분 | 기술(Technology) | 활용 목적 |
| :--- | :--- | :--- |
| **Backend** | `FastAPI`, `Python 3.12` | 고성능 비동기 API 서버 구축 |
| **AI Core** | `OpenAI GPT-4o-mini` | 텍스트 생성, 코드 분석, 의도 파악 |
| **LLM Ops** | `LangChain` | RAG 파이프라인 구축 및 프롬프트 체이닝 |
| **Database** | `ChromaDB` | 뉴스 및 채용 공고 벡터 임베딩 저장 및 검색 |
| **Crawling** | `Playwright`, `BeautifulSoup` | 동적 페이지(Iframe) 및 정적 페이지 크롤링 |
| **OCR** | `Tesseract (Pytesseract)` | 이미지형 채용 공고 텍스트 추출 |
| **Tools** | `ReportLab`, `SMTP` | PDF 문서 생성 및 이메일 전송 자동화 |

---

🚀 설치 및 실행 (How to Run)
1. 사전 요구 사항
Python 3.12 이상

Tesseract-OCR 설치 (Windows / Mac: brew install tesseract)

2. 프로젝트 클론 및 패키지 설치
Bash

git clone [REPOSITORY_URL]
cd NLP-BE

# 가상환경 생성 및 패키지 설치 (uv 사용 권장)
uv sync 
# 또는
pip install -r requirements.txt
3. 환경 변수 설정 (.env)
Ini, TOML

OPENAI_API_KEY=sk-proj-...
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
4. 서버 실행
Bash

uv run uvicorn main:app --reload
서버 실행 후 http://localhost:8000/docs 로 접속하여 API 문서를 확인할 수 있습니다.

👨‍💻 Author
Backend & AI Engineer: [본인 이름]

Email: [본인 이메일]

Github: [본인 깃허브 링크]