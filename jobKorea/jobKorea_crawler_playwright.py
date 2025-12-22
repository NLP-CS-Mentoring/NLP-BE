import asyncio
from playwright.async_api import async_playwright
import json
import requests
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from io import BytesIO

TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
KEYWORDS = ["개발자", "AI", "클라우드"]
PAGES_PER_KEYWORD = 5
RAW_FILE_NAME = "job_postings_raw.json"  
BASE_URL = "https://www.jobkorea.co.kr"

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def preprocess_image(img):
    width, height = img.size
    if height > 10000: scale_factor = 0.5
    elif height > 3000: scale_factor = 1.0
    elif height > 1000: scale_factor = 1.5
    else: scale_factor = 3.0

    if scale_factor != 1.0:
        img = img.resize((int(width*scale_factor), int(height*scale_factor)), Image.Resampling.LANCZOS)
    
    img = img.convert('L')
    img = img.filter(ImageFilter.SHARPEN)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0) 
    thresh = 170
    img = img.point(lambda x: 0 if x < thresh else 255, '1')
    return img

async def get_job_links(page, keyword, pages_to_scrape):
    links = []
    print(f"   └ 🔍 '{keyword}' 검색 시작...")

    for i in range(1, pages_to_scrape + 1):
        try:
            await page.goto(f"{BASE_URL}/Search/?stext={keyword}&tabType=recruit&Page_No={i}")
            try: await page.wait_for_load_state('networkidle', timeout=5000)
            except: pass
            
            job_links_els = await page.locator("a[href*='/Recruit/GI_Read/']").all()
            
            count = 0
            for link_el in job_links_els:
                try:
                    href = await link_el.get_attribute("href")
                    title = (await link_el.inner_text()).strip()
                    
                    if not href or len(title) < 2: continue
                    full_url = BASE_URL + href if not href.startswith("http") else href
                    
                    if not any(l['link'] == full_url for l in links):
                        links.append({
                            "company": "회사명 미상",
                            "title": title, 
                            "link": full_url
                        })
                        count += 1
                except: continue
            print(f"      [페이지 {i}] {count}개 공고 발견")
        except Exception as e:
            print(f"      ⚠️ 페이지 {i} 에러: {e}")
            
    return links

async def parse_job_detail(page, job_info):
    url = job_info['link']
    try:
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        company = "회사명 미상"
        if await page.locator(".coName").count() > 0:
            company = await page.locator(".coName").first.inner_text()
        elif await page.locator("div.header h1").count() > 0:
             company = await page.locator("div.header h1").first.inner_text()
        
        if company == "회사명 미상":
            page_title = await page.title()
            if "채용" in page_title: company = page_title.split("채용")[0].strip()
            elif "-" in page_title: company = page_title.split("-")[0].strip()

        final_company = company.strip()

        content_parts = []
        if await page.locator("dl.tbList").count() > 0:
            content_parts.append(await page.locator("dl.tbList").first.inner_text())

        extracted = False
        
        iframe_element = await page.query_selector('iframe[src*="GI_Read_Comt_Ifrm"]')
        if iframe_element:
            frame = await iframe_element.content_frame()
            if frame:
                await frame.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)

                try:
                    ft = await frame.inner_text("body")
                    if len(ft.strip()) > 50:
                        content_parts.append(ft.strip())
                        extracted = True
                except: pass

                images = await frame.query_selector_all('img')
                ocr_texts = []
                for img in images:
                    box = await img.bounding_box()
                    if not box: continue
                    if box['height'] > 150 or box['width'] > 400:
                        src = await img.get_attribute('src')
                        if src:
                            if src.startswith("//"): src = "https:" + src
                            elif src.startswith("/"): src = BASE_URL + src
                            
                            print(f"         📸 [OCR] 이미지 처리 중... ({int(box['width'])}x{int(box['height'])})")
                            try:
                                headers = {"User-Agent": "Mozilla/5.0"}
                                resp = requests.get(src, headers=headers, timeout=10)
                                img_data = Image.open(BytesIO(resp.content))
                                processed = preprocess_image(img_data)
                                text = pytesseract.image_to_string(processed, lang='kor+eng')
                                if len(text.strip()) > 20:
                                    ocr_texts.append(text)
                                    extracted = True
                            except: pass
                if ocr_texts: content_parts.append("\n".join(ocr_texts))

        if not extracted:
            selectors = [".art_txt", ".recruit-contents", ".st-container", "#gib_frame"]
            for sel in selectors:
                if await page.locator(sel).count() > 0:
                    text = await page.locator(sel).first.inner_text()
                    if len(text.strip()) > 50:
                        content_parts.append(text)
                        extracted = True
                        break

        final_content = "\n\n".join(content_parts)
        if len(final_content) < 50:
            final_content = f"(내용 추출 실패)\nLink: {url}"
            print(f"      ⚠️ 내용 추출 실패: {job_info['title']}")
        else:
            print(f"      ✅ 추출 성공 ({len(final_content)}자)")

        return {
            "company": final_company,
            "title": job_info['title'],
            "link": url,
            "content": final_content,
            "pubDate": "정보 없음"
        }

    except Exception as e:
        print(f"   [상세 실패] {url}: {e}")
        return None

async def main():
    print(f"🚀 [Step 1] 잡코리아 원본 데이터 수집")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()

        all_jobs = []
        print("\n--- 링크 수집 ---")
        for kw in KEYWORDS:
            jobs = await get_job_links(page, kw, PAGES_PER_KEYWORD)
            all_jobs.extend(jobs)
        
        unique_jobs = {v['link']: v for v in all_jobs}.values()
        print(f"\n✅ 총 {len(unique_jobs)}개 공고 상세 파싱 시작")

        results = []
        for i, job in enumerate(unique_jobs, 1):
            print(f"[{i}/{len(unique_jobs)}] {job['title'][:20]}... 처리 중")
            data = await parse_job_detail(page, job)
            if data: results.append(data)
        
        await browser.close()
    with open(RAW_FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n🎉 [Step 1 완료] '{RAW_FILE_NAME}' 생성됨 (회사명/제목 분리됨).")

if __name__ == "__main__":
    asyncio.run(main())