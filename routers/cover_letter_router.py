from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import hashlib
import time

# 만든 모듈 임포트
import schemas
from services.cover_letter.loader import load_text_from_file
from services.cover_letter.analyzer import analyze_style
from services.cover_letter.generator import generate_cover_letter
from services.cover_letter.cache import get_cached_style, set_cached_style

# ★ APIRouter 선언
router = APIRouter(
    prefix="/cover-letter",
    tags=["Cover Letter"]
)

# 1. 기본 자소서 생성 API
@router.post("/generate/basic")
def generate_basic_letter(req: schemas.BasicRequest):
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

# 2. 스타일 기반 자소서 생성 API (Redis 적용)
@router.post("/generate/with-style")
async def generate_styled_cover_letter(
    file: UploadFile = File(...),
    user_fact: str = Form(...)
):
    t0 = time.time()

    if not (file.filename.endswith('.pdf') or file.filename.endswith('.txt')):
        raise HTTPException(status_code=400, detail="PDF 또는 TXT 파일만 등록가능합니다.")

    try:
        # [Phase 1] 파일 읽기 및 해싱
        content = await file.read()
        file_hash = hashlib.sha256(content).hexdigest()
        t1 = time.time()
        phase_1 = t1 - t0

        # [Phase 2] Redis 캐시 확인
        cached_style = await get_cached_style(file_hash)
        
        if cached_style: # 캐시 히트
            style_result = cached_style
            t2 = time.time()
            phase_2 = t2 - t1
        else: # 캐시 미스
            raw_text = load_text_from_file(content, file.filename)
            style_result = analyze_style(raw_text)
            await set_cached_style(file_hash, style_result, expire=86400) # 24시간 저장
            t2 = time.time()
            phase_2 = t2 - t1
        
        # [Phase 3] 생성
        final_result = generate_cover_letter(user_fact=user_fact, style_guide=style_result)

        t3 = time.time()
        phase_3 = t3 - t2
        total_time = t3 - t0

        print(f"⏱️ Total: {total_time:.4f}s (Cache Hit: {bool(cached_style)})")

        return {
            "status": "success",
            "mode": "style_transfer",
            "analyzed_style": style_result,
            "result": final_result,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))