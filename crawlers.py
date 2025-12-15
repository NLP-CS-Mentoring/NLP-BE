import os
import re
import time
import json
import csv
import requests
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from dotenv import load_dotenv
load_dotenv()

NAVER_NEWS_API = "https://openapi.naver.com/v1/search/news.json"

def strip_tags(s: str) -> str:
    if not s:
        return s
    # 네이버 응답의 <b>...</b> 같은 태그 제거
    return re.sub(r"<[^>]+>", "", s)

def fetch_news(query: str, days: int = 14, display: int = 100, only_naver_news_link: bool = False):
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError("환경변수 NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 를 설정해 주세요.")

    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }

    # 한국(서울) 기준으로 컷오프 계산
    KST = timezone(timedelta(hours=9))
    cutoff = datetime.now(KST) - timedelta(days=days)

    results = []
    start = 1  # 1~1000
    while start <= 1000:
        params = {
            "query": query,
            "display": display,  # 최대 100
            "start": start,
            "sort": "date",      # 최신순
        }

        # 간단 재시도(서버 오류 등)
        for attempt in range(3):
            resp = requests.get(NAVER_NEWS_API, headers=headers, params=params, timeout=15)
            if resp.status_code >= 500:
                time.sleep(1.5 * (attempt + 1))
                continue
            resp.raise_for_status()
            break

        data = resp.json()
        items = data.get("items", [])
        if not items:
            break

        stop = False
        for it in items:
            pub = parsedate_to_datetime(it["pubDate"])  # RFC822 -> datetime
            if pub < cutoff:
                stop = True
                break

            link = it.get("link", "")
            if only_naver_news_link and "news.naver.com" not in link:
                continue

            results.append({
                "title": strip_tags(it.get("title", "")),
                "description": strip_tags(it.get("description", "")),
                "pubDate": pub.astimezone(KST).isoformat(),
                "link": link,
                "originallink": it.get("originallink", ""),
            })

        if stop:
            break

        start += display
        time.sleep(0.1)  # 호출 텀(너무 빠른 연속 호출 방지)

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
    news = fetch_news(query="IT", days=14, display=100, only_naver_news_link=False)
    print(f"수집 개수: {len(news)}")

    save_json("it_news_last_14_days.json", news)
    save_csv("it_news_last_14_days.csv", news)

    # 상위 5개만 미리보기
    for n in news[:5]:
        print(n["pubDate"], n["title"], n["link"])
