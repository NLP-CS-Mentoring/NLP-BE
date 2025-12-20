import asyncio
from playwright.async_api import async_playwright
import json
import random
import os

# ── [설정] 사용자 입력 없이 여기서 값 변경하세요 ──
KEYWORDS = ["개발자", "AI", "클라우드"]  # 검색할 키워드 리스트
PAGES_PER_KEYWORD = 2               # 키워드당 크롤링할 페이지 수
BASE_URL = "https://www.jobkorea.co.kr"
FILE_NAME = "job_postings.json"
# ──────────────────────────────────────────────

async def get_job_links(page, keyword, pages_to_scrape):
    """
    검색 결과 페이지에서 공고 링크를 수집합니다.
    (클래스 이름에 의존하지 않고 링크 패턴으로 찾습니다)
    """
    links = []
    print(f"   └ 🔍 '{keyword}' 검색 시작...")

    for i in range(1, pages_to_scrape + 1):
        try:
            # 잡코리아 검색 URL
            search_url = f"{BASE_URL}/Search/?stext={keyword}&tabType=recruit&Page_No={i}"
            
            # 페이지 이동
            await page.goto(search_url, wait_until="domcontentloaded")
            
            # 검색 결과가 로딩될 때까지 잠시 대기
            await page.wait_for_timeout(random.randint(2000, 4000))

            # ★ 핵심 수정: '/Recruit/GI_Read/'가 포함된 모든 a 태그 찾기
            # 특정 클래스(.post 등)에 의존하지 않고 링크 주소로만 찾습니다.
            job_links = await page.locator("a[href*='/Recruit/GI_Read/']").all()
            
            count_on_page = 0
            for link_el in job_links:
                # 1. 링크 주소 추출
                href = await link_el.get_attribute("href")
                
                # 2. 제목 추출 (a 태그 내부의 텍스트 전체를 가져와서 공백 제거)
                title_text = await link_el.inner_text()
                title = title_text.strip()
                
                # 제목이 너무 짧거나(회사명만 있는 경우 등), 링크가 없으면 건너뜀
                if not href or len(title) < 5:
                    continue
                
                # 중복 방지 (한 페이지 내 같은 공고가 여러 번 잡힐 수 있음)
                full_url = BASE_URL + href if not href.startswith("http") else href
                
                # 이미 리스트에 없는 경우만 추가
                if not any(l['url'] == full_url for l in links):
                    links.append({"title": title, "url": full_url})
                    count_on_page += 1
            
            print(f"      [페이지 {i}] {count_on_page}개 공고 발견")
            
            # 공고를 하나도 못 찾았다면, 봇 차단이나 로딩 실패일 수 있음
            if count_on_page == 0:
                print("      ⚠️ 공고를 찾지 못했습니다. (로딩 지연 또는 셀렉터 불일치)")

        except Exception as e:
            print(f"      [페이지 {i}] 에러 발생: {e}")
            
    return links

async def parse_job_detail(page, url):
    """
    상세 페이지 본문 파싱
    """
    try:
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(random.randint(1000, 2000))

        # 1. 회사명 추출 (여러 클래스 시도)
        company = "회사명 미상"
        co_locators = [".coName", ".co-name", "div.tb_cont .co_name"]
        for loc in co_locators:
            if await page.locator(loc).count() > 0:
                company = await page.locator(loc).first.inner_text()
                break
        
        # 2. 제목 추출
        title = ""
        # h3 태그 중 hd_ 클래스나 summary-tit 클래스 등을 찾음
        if await page.locator("h3.hd_").count() > 0:
            title = await page.locator("h3.hd_").first.inner_text()
        elif await page.locator(".summary-tit").count() > 0:
            title = await page.locator(".summary-tit").first.inner_text()
        
        if not title:
            title = await page.title()
            
        # 줄바꿈/공백 정리
        title = title.replace("\n", " ").strip()

        # 3. 본문 추출
        content_parts = []
        
        # (A) iframe 내부 텍스트 (잡코리아 구형 공고 대응)
        for frame in page.frames:
            try:
                # iframe 안에 body 텍스트가 충분히 길면 본문으로 간주
                text = await frame.inner_text("body")
                if len(text) > 100: 
                    content_parts.append(text)
            except:
                continue

        # (B) iframe이 아닌 일반 텍스트 영역
        # .art_txt: 구형 디자인 본문
        # .recruit-contents: 신형 디자인 본문
        # .detail-view: 또 다른 변형
        selectors = [".art_txt", ".recruit-contents", ".detail-view", "div.cont"]
        for sel in selectors:
            if await page.locator(sel).count() > 0:
                text = await page.locator(sel).first.inner_text()
                content_parts.append(text)
        
        # (C) 테이블형 정보 (우대사항, 자격요건 등이 표로 있는 경우)
        if await page.locator("dl.tbList").count() > 0:
            dl_text = await page.locator("dl.tbList").first.inner_text()
            content_parts.append(dl_text)

        # 텍스트 합치기
        full_content = "\n".join(content_parts)
        full_content = " ".join(full_content.split())
        
        if len(full_content) < 50:
            full_content = f"{title} - (본문 텍스트 추출 불가: 이미지 공고일 가능성 높음)"

        # 4. 날짜(마감일)
        pub_date = "정보 없음"
        if await page.locator(".date").count() > 0:
            pub_date = await page.locator(".date").first.inner_text()

        return {
            "title": f"[{company}] {title}",
            "link": url,
            "content": full_content,
            "pubDate": pub_date
        }

    except Exception as e:
        print(f"   [상세 실패] {url}: {e}")
        return None

async def main():
    print(f"🚀 Playwright 크롤러 시작 (키워드: {KEYWORDS})")
    print("   (브라우저를 띄워서 실행합니다...)")
    
    async with async_playwright() as p:
        # ★ headless=False로 변경: 브라우저가 뜨는 걸 눈으로 확인하세요! (차단 확률 ↓)
        browser = await p.chromium.launch(headless=False)
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()

        # 1. 링크 수집
        unique_jobs = {}
        print("\n--- [1단계] 링크 수집 ---")
        for kw in KEYWORDS:
            found_jobs = await get_job_links(page, kw, PAGES_PER_KEYWORD)
            for job in found_jobs:
                if job["url"] not in unique_jobs:
                    unique_jobs[job["url"]] = job["title"]
        
        total_count = len(unique_jobs)
        print(f"\n✅ 총 {total_count}개의 고유 공고 확보")
        
        if total_count == 0:
            print("❌ 공고를 하나도 못 찾았습니다. 브라우저 화면을 확인해보세요.")
            await browser.close()
            return

        # 2. 상세 내용 파싱
        job_data_list = []
        print("\n--- [2단계] 상세 내용 파싱 ---")
        for i, (url, title) in enumerate(unique_jobs.items(), 1):
            print(f"[{i}/{total_count}] {title[:20]}... 처리 중")
            data = await parse_job_detail(page, url)
            if data:
                job_data_list.append(data)
        
        await browser.close()

    # 3. 파일 저장
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(job_data_list, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 크롤링 완료! '{FILE_NAME}' 파일 생성됨.")

if __name__ == "__main__":
    asyncio.run(main())