import os
import json
import sys
from fastapi import APIRouter
from openai import OpenAI
from dotenv import load_dotenv

# [경로 설정]
# 현재 파일 위치를 기준으로 프로젝트 루트(NLP-BE)를 찾아 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

# [사용자 정의 모듈 임포트]
from services.tools import send_email_with_pdf, save_text_to_pdf
from schemas import AgentRequest  # ★ schemas.py에서 정의한 Pydantic 모델 사용

load_dotenv()

router = APIRouter(prefix="/agent", tags=["AI Agent"])

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ==========================================
# [시스템 프롬프트] - Brain: English / Mouth: Korean
# ==========================================
AGENT_SYSTEM_PROMPT = """
You are a smart AI assistant for cover letter management.
Your goal is to analyze the user's command and extract intent logically.

You must respond in **JSON format only**.

### Task
1. Analyze the user's input to understand their intent.
2. Check if the user provided **new cover letter text** directly in the chat.
3. Extract necessary information (action, email, new_content).

### Actions
- "save_pdf": User wants to download/save content as PDF.
- "send_email": User wants to send content via email.
- "none": User is just chatting, asking questions, or the input is unclear.

### Output JSON Structure
{
  "action": "save_pdf" | "send_email" | "none",
  "email": "string" | null,
  "new_content": "string" | null,
  "reply": "string" 
}

### Rules (IMPORTANT)
1. **Language**: The value of 'reply' MUST be in **Korean** (Natural, polite tone).
2. **New Content**: 
   - If the user explicitly types/pastes cover letter content (e.g., "Here is my intro: ...", "내용은 이거야: ..."), extract it into "new_content".
   - If the user just commands (e.g., "Save this as PDF"), set "new_content" to null.
3. **Email**:
   - If the user provides an email address, extract it.
   - If action is "send_email" but no address is found, set "email" to "".
4. **Reply**:
    - Write in a polite, helpful, and natural Korean tone.
   - For "save_pdf": Confirm that the file is being created.
   - For "send_email": Confirm that the email is being sent.
   - Do NOT mention internal file paths or technical IDs in the reply.
   - For "none": Answer the user's question naturally.
"""

@router.post("/execute")
async def execute_command(req: AgentRequest):
    """
    AI 에이전트 실행 엔드포인트
    - 입력: 사용자 메시지 + (선택) 현재 화면의 자소서 내용
    - 출력: AI 응답 + (필요시) 도구 실행 결과
    """
    user_message = req.message
    current_context = req.context or ""  # 없으면 빈 문자열 처리

    if not user_message:
        return {"type": "text", "content": "메시지를 입력해주세요."}

    # 1. GPT-4o-mini에게 판단 요청
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": f"User Input: {user_message}"}
            ],
            response_format={"type": "json_object"},  # JSON 모드 활성화
            temperature=0.3
        )
        
        # JSON 파싱
        ai_response = completion.choices[0].message.content
        decision = json.loads(ai_response)
        
        action = decision.get("action", "none")
        email = decision.get("email", "")
        new_content_from_chat = decision.get("new_content")  # 채팅에서 추출한 새 내용
        reply = decision.get("reply", "요청을 처리해 드릴게요.")

    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return {"type": "text", "content": "죄송해요, AI 판단 중에 오류가 발생했어요."}

    # ==================================================
    # ★ 핵심 로직: [우선순위] 채팅 내용 > 화면 내용
    # ==================================================
    final_content = ""
    
    if new_content_from_chat:
        # 사용자가 방금 채팅으로 내용을 줬다면 그걸 최우선으로 사용
        final_content = new_content_from_chat
    elif current_context:
        # 그게 아니면 현재 화면에 떠 있는 내용을 사용
        final_content = current_context
    
    # --------------------------------------------------

    # [CASE A] PDF 저장
    if action == "save_pdf":
        if not final_content:
            return {"type": "text", "content": "저장할 내용이 없어요. 내용을 입력해주시거나 자소서를 먼저 작성해주세요."}
        
        try:
            # 1. 파일 생성 (여기서 path는 C:\Users\... 절대경로)
            full_path = save_text_to_pdf(final_content)
            
            # 2. 파일명만 쏙 빼내기 (예: cover_letter_20251221.pdf)
            filename = os.path.basename(full_path)
            
            # 3. 접속 가능한 URL 만들기 (아까 main.py에서 만든 /downloads 경로 활용)
            download_url = f"/downloads/{filename}" # 프론트엔드에서 쓸 주소

            # 4. 프론트엔드에 '이건 파일이야!'라고 알려주기
            return {
                "type": "file",           # ★ 프론트가 이거 보고 "어? 파일이네? 버튼 띄워야지" 판단함
                "content": reply,         # "네, PDF로 저장했습니다."
                "url": download_url,      # 다운로드 링크
                "filename": filename      # 파일 이름 (보여주기용)
            }
            
        except Exception as tool_err:
            return {"type": "text", "content": f"PDF 생성 중 오류가 났어요: {tool_err}"}

    # [CASE B] 이메일 전송
    elif action == "send_email":
        if not final_content:
            return {"type": "text", "content": "보낼 내용이 없습니다."}
        
        if not email:
            # 이메일 주소가 없으면 AI가 다시 물어보게 유도 (reply 활용)
            return {"type": "text", "content": "이메일 주소를 알려주시면 바로 보내드릴게요!"}
        
        # 이메일 전송 도구 호출
        tool_result = send_email_with_pdf(email, "[AI 채용비서] 요청하신 자소서 파일", "안녕하세요, 요청하신 파일 첨부드립니다.", final_content)
        
        return {"type": "text", "content": f"{reply} ({tool_result})"}

    # [CASE C] 일반 대화 (none)
    else:
        return {"type": "text", "content": reply}