import json
import time
import os
from dotenv import load_dotenv, find_dotenv
from groq import Groq

load_dotenv(find_dotenv())

RAW_FILE_NAME = "job_postings_raw.json"      
FINAL_FILE_NAME = "job_postings_final.json"   
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def clean_text_with_groq(client, raw_text):
    if not raw_text or len(raw_text) < 50 or "실패" in raw_text:
        return raw_text

    prompt = f"""
    너는 '채용 공고 데이터 추출 전문가'야. 
    제공된 텍스트는 이미지 OCR 결과물로, 심각한 노이즈와 채용과 무관한 잡담(인터뷰, 회사자랑)이 섞여 있어.
    
    [미션]
    쓰레기 데이터 속에서 **진짜 채용 정보**만 발굴하여 구조화해라.

    [강력한 무시 규칙 (반드시 지킬 것)]
    1. **회사 연혁(History), 직원 인터뷰(Q&A), 복지 자랑, 감성적인 멘트**는 전부 무시하고 삭제해.
    2. 'HOTSELLER', 'wee', '00 |' 같은 깨진 글자나 의미 없는 특수문자는 삭제해.

    [추출해야 할 항목]
    아래 5가지 항목을 찾아서 정리해. 정보가 없으면 '내용 없음'으로 적어.
    
    1. **기술 스택**: 언어, 프레임워크, 툴 (예: Python, React, AWS)
    2. **주요 업무**: 구체적으로 무슨 일을 하는지
    3. **자격 요건**: 경력 연수, 필수 경험
    4. **우대 사항**: 있으면 좋은 기술이나 경험
    5. **근무 조건**: 연봉, 근무지, 근무 시간

    [출력 형식]
    - 서론, 결론 없이 오직 결과 데이터만 출력해.
    - 한국어로 출력해.

    [원본 텍스트]
    {raw_text[:6000]} 
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a strict data extractor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=2000,
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Groq API 에러: {e}")
        return raw_text

def main():
    print(f"🚀 [Step 2] Groq AI 데이터 정제 및 분리 저장")
    
    if not GROQ_API_KEY:
        print("오류: .env 파일에 GROQ_API_KEY가 없습니다.")
        return

    try:
        with open(RAW_FILE_NAME, "r", encoding="utf-8") as f:
            jobs = json.load(f)
    except FileNotFoundError:
        print(f"'{RAW_FILE_NAME}' 파일이 없습니다. Step 1을 먼저 실행하세요.")
        return

    client = Groq(api_key=GROQ_API_KEY)
    final_results = []

    print(f"총 {len(jobs)}개 공고 정제 시작...")

    for i, job in enumerate(jobs, 1):
       
        print(f"[{i}/{len(jobs)}] {job['company']} - {job['title'][:20]}... 처리 중")
        
        original_content = job['content']
        
        if len(original_content) < 50 or "실패" in original_content:
            cleaned_content = original_content
            print("      PASS (내용 부족)")
        else:
            cleaned_content = clean_text_with_groq(client, original_content)
            time.sleep(2) 

        processed_job = {
            "company": job['company'],
            "title": job['title'],
            "link": job['link'],
            "content": cleaned_content, 
            "pubDate": job['pubDate']
        }
        final_results.append(processed_job)

    with open(FINAL_FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(final_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n[Step 2 완료] '{FINAL_FILE_NAME}' 파일에 저장되었습니다.")

if __name__ == "__main__":
    main()
    
