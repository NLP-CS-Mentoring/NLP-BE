# 🤖 AI Career Assistant Backend Service
> **"취업 준비의 A to Z를 돕는 지능형 AI 에이전트 서비스"** > 최신 뉴스 요약, 채용 공고 기반 학습 로드맵 제안, 그리고 자소서 관리(PDF/Email) 자동화 기능을 제공하는 FastAPI 기반 백엔드 프로젝트입니다.

---

## 📖 프로젝트 개요
이 프로젝트는 IT 분야 취업 준비생들이 겪는 정보 비대칭과 반복적인 작업을 해결하기 위해 개발되었습니다.  
**LangChain**과 **GPT-4o-mini**를 활용하여 단순한 답변 생성을 넘어, 실제 **채용 공고를 분석(RAG)**하고 사용자의 명령을 수행하는 **Action Agent**를 구현했습니다.

### 🎯 핵심 목표
1. **Intelligence**: 사용자의 불명확한 의도를 파악하고 맥락(Context)을 이해하는 AI.
2. **Automation**: 자소서 PDF 변환, 이메일 전송 등 반복 업무 자동화.
3. **Data-Driven**: 실제 잡코리아 채용 공고와 네이버 뉴스를 크롤링하여 실시간 트렌드 반영.

---

## 🚀 주요 기능 (Key Features)

### 1. 🧠 Context-Aware AI Agent (자소서 비서)
단순한 챗봇이 아닌, 사용자의 **현재 화면(Context)**과 **채팅 명령**을 구분하여 판단하는 에이전트입니다.
- **기능**: 자소서 작성 보조, PDF 자동 변환 및 다운로드, 이메일 전송.
- **기술**: 
  - `GPT-4o-mini`의 **JSON Mode**를 활용하여 완벽한 구조화된 데이터(JSON) 출력.
  - **System Prompt Engineering**: 사고(Thinking)는 영어로 논리적으로, 답변(Reply)은 자연스러운 한국어로 출력.
  - **Priority Logic**: 사용자가 새로 입력한 내용 vs 기존 화면 내용을 구분하여 처리.

### 2. 🗺️ 커리어 로드맵 추천 (RAG Pipeline)
사용자가 희망 직무(예: "AI 엔지니어")를 입력하면, 실제 채용 공고를 분석하여 학습 방향을 제시합니다.
- **데이터 수집**: `Playwright`를 사용해 **잡코리아** 공고 크롤링.
- **이미지 OCR**: 텍스트 없이 통이미지로 된 공고도 `Tesseract-OCR`로 텍스트 추출.
- **RAG 구현**: 
  - `LangChain` + `ChromaDB`를 활용한 벡터 검색.
  - 검색된 공고들의 공통 요구사항을 분석하여 **"가장 많이 요구하는 기술 스택"**과 **"학습 로드맵"** 도출.

### 3. 📰 최신 IT 트렌드 요약
- **데이터 수집**: `BeautifulSoup`을 활용한 **네이버 뉴스** 크롤링.
- **AI 요약**: 뉴스 본문을 AI가 읽고 핵심 내용만 요약하여 제공.

---

## 🛠️ 기술 스택 (Tech Stack)

### Backend
- **Framework**: `FastAPI` (비동기 처리 및 빠른 API 개발)
- **Language**: Python 3.12+

### AI & LLM
- **LLM**: `OpenAI GPT-4o-mini` (가성비와 성능 최적화)
- **Orchestration**: `LangChain` (LCEL 문법을 활용한 RAG 파이프라인 구축)
- **Vector DB**: `ChromaDB` (임베딩 데이터 저장)

### Crawler & Automation
- **Web Browser**: `Playwright` (동적 페이지 크롤링)
- **OCR**: `Pytesseract` (이미지 텍스트 추출)
- **Document**: `ReportLab` (PDF 생성 및 한글 자동 줄바꿈 처리)

### Infra & Tools
- **Deployment**: (배포 환경이 있다면 기재, 예: AWS EC2 / Docker)
- **Environment**: `uv` (패키지 관리), `dotenv`

---

## 📂 프로젝트 구조 (Project Structure)
```bash
NLP-BE/
├── main.py                  # 앱 진입점 (Lifespan, Static Mount 설정)
├── routers/                 # API 엔드포인트 분리
│   ├── agent_router.py      # AI 에이전트 (판단 및 도구 실행)
│   ├── news_career_router.py # 뉴스 및 로드맵 RAG
│   └── cover_letter_router.py
├── services/                # 핵심 비즈니스 로직
│   ├── tools.py             # PDF 생성, 이메일 전송
│   
├── schemas.py               # Pydantic 데이터 모델 (Request/Response)
├── outputs/                 # 생성된 PDF 파일 저장소
├── jobKorea_chroma_db/      # 벡터 DB 저장소
└── news_chroma_db/          # 벡터 DB 저장소