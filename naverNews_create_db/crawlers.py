import os
import re
import time
import json
import csv
import requests
import html  # [NEW] HTML 엔티티 처리를 위해 추가
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup 
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

NAVER_NEWS_API = "https://openapi.naver.com/v1/search/news.json"

def strip_tags(s: str) -> str:
    """
    HTML 태그를 제거하고, &quot; 같은 불필요한 엔티티를 정리합니다.
    """
    if not s:
        return s
    
    # 1. HTML 태그 제거 (<br>, <b> 등)
    s = re.sub(r"<[^>]+>", "", s)
    
    # 2. [요청 사항 반영] &quot; 및 기타 HTML 엔티티 처리
    # 사용자가 '삭제'를 원했으므로 공백으로 치환하거나, 
    # 원래 문자인 쌍따옴표(")로 복원할 수 있습니다.
    # 여기서는 읽기 편하게 원래 문자(")로 복원하고, 불필요한 기호를 정리합니다.
    s = html.unescape(s)  # &quot; -> ", &lt; -> < 등으로 자동 변환
    
    # 혹시 남아있을 수 있는 쓰레기 값 제거 (필요 시 추가)
    s = s.replace("&quot;", "") 
    
    return s.strip()

# --- 금융/주식 뉴스 필터링 함수 ---
def is_financial_or_irrelevant(text: str) -> bool:
    """
    제목이나 내용에 주식/금융 관련 키워드가 있으면 True를 반환합니다.
    (개발자에게 불필요한 노이즈 제거용)
    """
    stop_words = [
        "코스닥", "코스피", "상장", "주가", "매수", "목표가", "금융위", "특례", 
        "영업이익", "매출", "전년비", "배당", "ETF", "증권", "금리", "마감", 
        "체결", "약세", "강세", "급등", "급락", "투자주의", "공시", "테마주"
    ]
    
    for word in stop_words:
        if word in text:
            return True # 금융 뉴스임 (삭제 대상)
    return False # 수집 대상

def get_naver_news_content(url: str) -> str:
    """
    네이버 뉴스 상세 페이지의 본문을 크롤링합니다.
    """
    if "news.naver.com" not in url:
        return "" 

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 네이버 뉴스 본문 selector 모음
        content_div = soup.select_one("#dic_area")
        if not content_div:
            content_div = soup.select_one("#articeBody")
        if not content_div:
            content_div = soup.select_one("#newsct_article")

        if content_div:
            text = content_div.get_text(separator="\n", strip=True)
            return strip_tags(text) # 본문에도 태그 제거 적용
        else:
            return "" 

    except Exception:
        return ""

def fetch_news(query: str, days: int = 14, display: int = 100, only_naver_news_link: bool = False):
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise RuntimeError("환경변수 NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 를 설정해 주세요.")

    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }

    KST = timezone(timedelta(hours=9))
    cutoff = datetime.now(KST) - timedelta(days=days)

    results = []
    start = 1
    
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # 키워드 하나당 최대 300개까지만 검색 (조절 가능)
    while start <= 300:
        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort": "date",
        }

        try:
            resp = requests.get(NAVER_NEWS_API, headers=headers, params=params, timeout=10, verify=False)
            resp.raise_for_status()
        except Exception as e:
            print(f"⚠️ API 요청 실패 ({query}): {e}")
            break

        data = resp.json()
        items = data.get("items", [])
        if not items:
            break

        stop_fetching = False
        
        for it in items:
            pub = parsedate_to_datetime(it["pubDate"])
            if pub < cutoff:
                stop_fetching = True
                break

            link = it.get("link", "")
            title = strip_tags(it.get("title", "")) # 제목 정제 ( &quot; 제거됨 )
            
            # [필터링 1] 제목 금융 키워드 검사
            if is_financial_or_irrelevant(title):
                continue

            is_naver_news = "news.naver.com" in link
            if only_naver_news_link and not is_naver_news:
                continue

            # 본문 크롤링
            content = ""
            if is_naver_news:
                content = get_naver_news_content(link)
                time.sleep(0.1) # 텀을 짧게 (0.1초)
            
            # [필터링 2] 본문 검사
            if len(content) < 100: 
                continue
            if is_financial_or_irrelevant(content): 
                continue

            results.append({
                "title": title,
                "description": strip_tags(it.get("description", "")),
                "content": content, 
                "pubDate": pub.astimezone(KST).isoformat(),
                "link": link,
                "originallink": it.get("originallink", ""),
            })

        if stop_fetching:
            break

        start += display
        time.sleep(0.3) 

    return results

def save_json(path: str, rows):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

def save_csv(path: str, rows):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

if __name__ == "__main__":
    # 1. 검색어 리스트 정의 (분야별 균형 수집)
    search_keywords = [
        # AI / 신기술
        "생성형 AI", "LLM", "AI 에이전트", "피지컬 AI",
        # 개발 트렌드 / 커리어
        "개발자 채용", "소프트웨어 개발", "오픈소스",
        # 프론트 / 백엔드 / 클라우드
        "프론트엔드 트렌드", "백엔드 개발", "클라우드"
    ]
    
    print(f"🚀 총 {len(search_keywords)}개의 키워드로 뉴스 수집을 시작합니다.")
    
    all_news_data = []

    # 2. 키워드별 반복 수집
    for keyword in search_keywords:
        print(f"🔍 '{keyword}' 검색 중...")
        
        # days=7 (최근 7일), display=100 (한 번에 100개 요청)
        news_items = fetch_news(query=keyword, days=7, display=100, only_naver_news_link=True)
        
        print(f"   -> {len(news_items)}개 수집 완료")
        all_news_data.extend(news_items)

    # 3. 중복 제거 (여러 키워드에 겹친 기사 삭제)
    # 딕셔너리를 이용해 'link'가 같으면 하나만 남김
    unique_news_map = {item['link']: item for item in all_news_data}
    final_news_list = list(unique_news_map.values())

    print(f"\n✅ 최종 정리 완료: 총 {len(final_news_list)}건 (중복 {len(all_news_data) - len(final_news_list)}건 제거됨)")

    if final_news_list:
        save_json("it_news_with_content.json", final_news_list)
        save_csv("it_news_with_content.csv", final_news_list)

        print("\n[상위 3개 기사 미리보기]")
        for n in final_news_list[:3]:
            print(f"- {n['title']}")
    else:
        print("수집된 뉴스가 없습니다.")