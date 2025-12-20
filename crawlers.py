import os
import re
import time
import json
import csv
import requests
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup 

from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

NAVER_NEWS_API = "https://openapi.naver.com/v1/search/news.json"

def strip_tags(s: str) -> str:
    if not s:
        return s
    return re.sub(r"<[^>]+>", "", s)

# --- [NEW] 금융/주식 뉴스 필터링 함수 ---
def is_financial_or_irrelevant(text: str) -> bool:
    """
    제목이나 내용에 주식/금융 관련 키워드가 있으면 True를 반환합니다.
    (개발자에게 불필요한 노이즈 제거용)
    """
    # 제외할 키워드 리스트 (주식, 금융, 부동산, 단순 사건사고 등)
    stop_words = [
        "코스닥", "코스피", "상장", "주가", "매수", "목표가", "금융위", "특례", 
        "영업이익", "매출", "전년비", "배당", "ETF", "증권", "금리", "마감", 
        "체결", "약세", "강세", "급등", "급락", "투자주의", "공시"
    ]
    
    for word in stop_words:
        if word in text:
            return True # 금융 뉴스임
    return False # 금융 뉴스 아님 (수집 대상)

def get_naver_news_content(url: str) -> str:
    """
    네이버 뉴스 상세 페이지(news.naver.com)의 본문을 크롤링합니다.
    """
    if "news.naver.com" not in url:
        return "" 

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False) # SSL 에러 방지용 verify=False
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        content_div = soup.select_one("#dic_area")
        if not content_div:
            content_div = soup.select_one("#articeBody")
        if not content_div:
            content_div = soup.select_one("#newsct_article")

        if content_div:
            return content_div.get_text(separator="\n", strip=True)
        else:
            return "" 

    except Exception as e:
        # print(f"Error fetching content from {url}: {e}") # 로그가 너무 많으면 주석 처리
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
    
    # SSL 경고 숨기기 (verify=False 사용 시 깔끔하게 보이기 위함)
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # 최대 500개 정도만 검색 (너무 많으면 오래 걸림)
    while start <= 500:
        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort": "date",
        }

        for attempt in range(3):
            try:
                resp = requests.get(NAVER_NEWS_API, headers=headers, params=params, timeout=15, verify=False)
                if resp.status_code >= 500:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                resp.raise_for_status()
                break
            except Exception as e:
                print(f"API Request failed: {e}")
                if attempt == 2: return results 

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
            title = strip_tags(it.get("title", ""))
            
            # --- [필터링 1단계] 제목에 금융 키워드가 있으면 스킵 ---
            if is_financial_or_irrelevant(title):
                continue
            # --------------------------------------------------

            is_naver_news = "news.naver.com" in link
            if only_naver_news_link and not is_naver_news:
                continue

            # --- 본문 크롤링 ---
            content = ""
            if is_naver_news:
                try:
                    content = get_naver_news_content(link)
                except Exception as e:
                    content = ""
                
                time.sleep(0.2) # 텀을 조금 줄임 (속도 향상)
            
            # --- [필터링 2단계] 본문이 없거나, 너무 짧거나, 본문에 금융 내용이 많으면 스킵 ---
            if len(content) < 100: # 본문이 너무 짧은 경우 제외
                continue
                
            if is_financial_or_irrelevant(content): # 본문 내용도 한번 더 검사
                continue
            # --------------------------------------------------

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
        time.sleep(0.4) 

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
    # 검색어를 좀 더 구체적으로 변경 (IT -> 인공지능 개발)
    # 여러 키워드를 합쳐서 검색하고 싶으면 "생성형 AI | 오픈소스 | 개발자" 처럼 |(OR) 연산자 사용 가능
    search_query = "생성형 AI | 소프트웨어 개발 | 클라우드 기술"
    
    print(f"검색어 [{search_query}]로 뉴스 수집 시작...")
    
    # days=2 (최근 2일치만 - RAG 분석용은 최신성이 중요하므로 짧게)
    news = fetch_news(query=search_query, days=2, display=100, only_naver_news_link=True)
    
    print(f"🧹 정제 후 수집 완료: {len(news)}건")

    if news:
        save_json("it_news_with_content.json", news)
        save_csv("it_news_with_content.csv", news)

        # 상위 3개 미리보기
        print("\n[수집된 기사 예시]")
        for n in news[:3]:
            print(f"- {n['title']}")
    else:
        print("수집된 뉴스가 없습니다.")