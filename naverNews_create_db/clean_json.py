import json
import os
import html

INPUT_FILE = "it_news_with_content.json"  # 원본 파일명
OUTPUT_FILE = "it_news_cleaned.json"      # 저장할 파일명 

def clean_text(text):
    if not text:
        return ""
    
    # &quot; 문자열을 삭제
    text = text.replace("&quot;", "")
    
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    
    return text

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ {INPUT_FILE} 파일이 없습니다.")
        return

    # 1. 파일 읽기
    print(f"📂 {INPUT_FILE} 로딩 중...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 2. 데이터 정제
    print("🧹 데이터 청소 중...")
    count = 0
    for item in data:
        # 제목 정제
        if "title" in item:
            original = item['title']
            cleaned = clean_text(original)
            
            if original != cleaned:
                item['title'] = cleaned
                count += 1
        
        # 본문 정제
        if "content" in item:
            item['content'] = clean_text(item['content'])
        if "description" in item:
            item['description'] = clean_text(item['description'])

    # 3. 파일 저장
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        # ensure_ascii=False를 해야 한글이 안 깨짐
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✨ 완료! 총 {count}개의 제목을 수정했습니다.")
    print(f"💾 결과가 '{OUTPUT_FILE}'에 저장되었습니다.")

if __name__ == "__main__":
    main()