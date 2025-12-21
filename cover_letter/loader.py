# 파일 읽기
import pdfplumber
import io

def load_text_from_file(file_content: bytes, filename: str) -> str:
    """ 
    바이트로 받아 텍스트 추출 -> 
    """
    text = ""
    
    try:
        if filename.endswith('.pdf'):
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
                        
        if filename.endswith('.txt'):
            text = file_content.decode("utf-8")
            
        return text.strip()
    
    except Exception as e: # 파일 읽다가 에러
        print(f"Error reading file: {e}")
        return ""
