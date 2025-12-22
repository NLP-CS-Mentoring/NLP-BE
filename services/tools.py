import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
from dotenv import load_dotenv

# PDF 생성 관련 라이브러리
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit  
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))     
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "outputs")      
FONTS_DIR = os.path.join(BASE_DIR, "..", "fonts")             

FONT_FILENAME = "Malgun.ttf" 
FONT_PATH = os.path.join(FONTS_DIR, FONT_FILENAME)
FONT_NAME = "MyKoreanFont"  

try:
    if os.path.exists(FONT_PATH):
        # 폰트 파일이 있으면 등록
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
        print(f"✅ 한글 폰트 로드 성공: {FONT_PATH}")
    else:
        # 파일이 없으면 에러 발생시켜서 except로 넘김
        raise FileNotFoundError(f"폰트 파일이 없습니다: {FONT_PATH}")
except Exception as e:
    # 폰트 로드 실패 시 기본 폰트(영문 전용) 사용
    print(f"⚠️ Warning: 한글 폰트 로드 실패 ({e})")
    print("   -> 기본 폰트(Helvetica)를 사용합니다. 한글이 깨질 수 있습니다.")
    FONT_NAME = "Helvetica"


def _ensure_output_dir() -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return OUTPUT_DIR


def save_text_to_pdf(content: str) -> str:
    """
    텍스트 내용을 PDF로 저장하고 파일 경로를 반환합니다.
    (자동 줄바꿈 기능 추가 완료)
    """
    _ensure_output_dir()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"cover_letter_{ts}.pdf"
    path = os.path.join(OUTPUT_DIR, filename)

    # PDF 캔버스 생성
    p = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    
    # 폰트 설정
    font_size = 11
    p.setFont(FONT_NAME, font_size)

    # 여백 및 줄 간격 설정
    left_margin = 40
    right_margin = 40
    y = height - 40
    line_height = 20
    
    # 글자가 들어갈 수 있는 최대 가로 폭 계산
    max_width = width - (left_margin + right_margin)

    # 텍스트 줄바꿈 처리
    # 1. 원본 텍스트의 엔터(줄바꿈) 기준으로 먼저 나눔
    paragraphs = content.splitlines()

    for paragraph in paragraphs:
        # 2. 각 문단이 가로 폭(max_width)을 넘어가면 자동으로 쪼개줌 (Wrapping)
        # simpleSplit(텍스트, 폰트이름, 폰트크기, 최대폭)
        wrapped_lines = simpleSplit(paragraph, FONT_NAME, font_size, max_width)

        # 쪼개진 줄들을 하나씩 그리기
        for line in wrapped_lines:
            # 페이지 공간 부족하면 다음 장으로
            if y < 40:
                p.showPage()
                p.setFont(FONT_NAME, font_size) # 새 페이지 폰트 재설정
                y = height - 40
            
            p.drawString(left_margin, y, line)
            y -= line_height # 다음 줄로 이동

    p.save()
    return path


def send_email_with_pdf(
    to_email: str,
    subject: str,
    body: str,
    content: str
) -> str:
    """
    내용(content)을 PDF로 변환하여 저장한 뒤, 이메일에 첨부하여 전송합니다.
    """
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_user or not smtp_password:
        return "Error: .env 파일에 SMTP 설정이 없습니다."

    try:
        # 1. PDF 생성
        file_path = save_text_to_pdf(content)
        filename = os.path.basename(file_path)

        # 2. PDF 파일 읽기
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        # 3. 이메일 구성
        msg = EmailMessage()
        msg["From"] = smtp_user
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)

        # 4. 파일 첨부
        msg.add_attachment(
            file_bytes,
            maintype="application",
            subtype="pdf",
            filename=filename,
        )

        # 5. 전송 (Gmail SSL 기준)
        # 네이버 메일 등은 smtp.naver.com / 465 또는 587 사용
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(msg)

        return f"성공: {to_email}로 PDF({filename})를 보냈습니다."

    except Exception as e:
        return f"실패: 이메일 전송 중 에러가 발생했습니다. ({str(e)})"