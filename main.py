# ------------------------------- 인 메모리 사용(v1) --------------------------------------
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from cover_letter.loader import load_text_from_file
from cover_letter.analyzer import analyze_style
from cover_letter.generator import generate_cover_letter

import hashlib
import time

load_dotenv()
# uv run python -m uvicorn main:app
# 파일 받고 스타일 분석하는 부분을 캐시를 사용해서 응답 속도 늘리기 위함(약 53%정도 속도 개선)
# 파일 캐시 저장소 -> redis로 변경 main_redis.py 참조
CACHE = {}
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BasicRequest(BaseModel):
    user_fact: str # 사용자 입력

# 1. 기본 자소서 생성 API (파일 X)
@app.post("/generate/basic")
def generate_basic_letter(req: BasicRequest):
    """
    파일 없이 사용자의 경험만 받아 표준 스타일로 자소서를 생성
    """
    if not req.user_fact:
        raise HTTPException(status_code=400, detail="user_fact is empty")

    try:
        result = generate_cover_letter(user_fact=req.user_fact, style_guide=None)
        
        return {
            "status": "success",
            "mode": "basic",
            "result": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. 스타일 기반 자소서 생성 API (파일 O)
@app.post("/generate/with-style")
async def generate_styled_cover_letter(
    file: UploadFile = File(...),
    user_fact: str = Form(...)
):
    """
    파일을 포함해 PDF나 TXT 파일을 업로드받아 말투를 분석한 후, 그 스타일로 자소서를 생성
    """

    t0 = time.time()

    if not (file.filename.endswith('.pdf') or file.filename.endswith('.txt')):
        raise HTTPException(status_code=400, detail="PDF 또는 TXT 파일만 등록가능합니다.")

    try:
        # [Phase 1]
        content = await file.read()
        file_hash = hashlib.sha256(content).hexdigest()

        t1 = time.time()
        phase_1 = t1 - t0

        # [Phase 2]
        if file_hash in CACHE: # 캐시 히트
            style_result = CACHE[file_hash]

            t2 = time.time()
            phase_2 = t2 - t1
        else: # 캐시 미스
            raw_text = load_text_from_file(content, file.filename) # pdf나 txt로 부터 텍스트 읽어오기
            style_result = analyze_style(raw_text) # 스타일 분석
            CACHE[file_hash] = style_result

            t2 = time.time()
            phase_2 = t2 - t1
        
        # [Phase 3]
        final_result = generate_cover_letter(user_fact=user_fact, style_guide=style_result) # 자소서 생성

        t3 = time.time()
        phase_3 = t3 - t2
        total_time = t3 - t0

        print(f"total_time: {round(total_time, 4)}, phase_1: {round(phase_1, 4)}, phase_2: {round(phase_2, 4)}, phase_3: {round(phase_3, 4)}")
        # total_time(캐시 미스): 10.9809, phase_1: 0.0022, phase_2: 4.7772, phase_3: 6.2015
        # total_time(캐시 히트): 7.13, phase_1: 0.0021, phase_2: 0.0, phase_3: 7.1279

        return {
            "status": "success",
            "mode": "style_transfer",
            "analyzed_style": style_result,
            "result": final_result,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
