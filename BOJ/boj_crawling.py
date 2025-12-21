from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterable, List, Dict

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
SEED_PATH = BASE_DIR.parent / "services" / "Algorithm" / "problems_seed.json"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 크롤링할 백준 문제집 URL 목록
WORKBOOK_URLS = [
	"https://www.acmicpc.net/workbook/view/1152",
	"https://www.acmicpc.net/workbook/view/8708",
	"https://www.acmicpc.net/workbook/view/4349",
    "https://www.acmicpc.net/workbook/view/4357",
    "https://www.acmicpc.net/workbook/view/140",
    "https://www.acmicpc.net/workbook/view/2418"
]


_SESSION = requests.Session()
_SESSION.headers.update(
	{
		"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
		"Accept-Language": "ko,en;q=0.9",
		"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
	}
)


def fetch_problem_html(problem_id: int) -> str:
	url = f"https://www.acmicpc.net/problem/{problem_id}"
	resp = _SESSION.get(url, timeout=10)
	resp.raise_for_status()
	return resp.text


def fetch_workbook_problem_ids(workbook_url: str) -> List[int]:
	"""Extract problem IDs from a Baekjoon workbook page."""
	resp = _SESSION.get(workbook_url, timeout=10)
	resp.raise_for_status()
	soup = BeautifulSoup(resp.text, "html.parser")
	
	problem_ids = []
	# 문제집 페이지의 문제 링크 파싱
	for link in soup.select("a[href^='/problem/']"):
		href = link.get("href", "")
		if href.startswith("/problem/"):
			try:
				pid = int(href.split("/")[-1])
				if pid not in problem_ids:
					problem_ids.append(pid)
			except (ValueError, IndexError):
				continue
	
	return problem_ids


def parse_problem(problem_id: int, html: str) -> Dict[str, str]:
	soup = BeautifulSoup(html, "html.parser")
	title_el = soup.select_one("#problem_title")
	desc_el = soup.select_one("#problem_description") or soup.select_one(".problem-text")
	if not title_el or not desc_el:
		raise ValueError("Failed to parse problem title/description")

	title = title_el.get_text(strip=True)
	statement = desc_el.get_text("\n", strip=True)

	return {
		"id": f"bj-{problem_id}",
		"title": title,
		"source": f"Baekjoon {problem_id}",
		"url": f"https://www.acmicpc.net/problem/{problem_id}",
		"statement": statement,
	}


def call_gemini(statement: str) -> Dict[str, object]:
	if not OPENAI_API_KEY:
		print("[!] Warning: OPENAI_API_KEY not found. Skipping LLM analysis.")
		return {"tags": [], "solution_outline": ""}

	client = OpenAI(api_key=OPENAI_API_KEY)
	sys_prompt = (
		"You extract algorithm tags and a brief solution outline from Baekjoon problem statements."
		" Output JSON only with keys: tags (array of 3-5 short algorithm tags) and solution_outline (<= 400 characters, Korean OK)."
	)
	
	try:
		resp = client.chat.completions.create(
			model="gpt-4o-mini",
			temperature=0.2,
			response_format={"type": "json_object"},
			messages=[
				{"role": "system", "content": sys_prompt},
				{"role": "user", "content": statement},
			],
		)
		parsed = json.loads(resp.choices[0].message.content)
		tags = [str(t).strip() for t in parsed.get("tags", []) if str(t).strip()]
		outline = (parsed.get("solution_outline") or "").strip()
		return {"tags": tags, "solution_outline": outline}
	except Exception as e:
		print(f"[!] OpenAI API error: {e}")
		return {"tags": [], "solution_outline": ""}


def build_item(problem_id: int) -> Dict[str, object]:
	html = fetch_problem_html(problem_id)
	base = parse_problem(problem_id, html)
	extra = call_gemini(base["statement"])
	base["tags"] = extra.get("tags", [])
	base["solution_outline"] = extra.get("solution_outline", "")
	return base


def load_existing() -> List[Dict[str, object]]:
	if not SEED_PATH.exists():
		return []
	with open(SEED_PATH, "r", encoding="utf-8") as f:
		try:
			return json.load(f)
		except Exception:
			return []


def save_seed(items: List[Dict[str, object]]):
	SEED_PATH.parent.mkdir(parents=True, exist_ok=True)
	with open(SEED_PATH, "w", encoding="utf-8") as f:
		json.dump(items, f, ensure_ascii=False, indent=2)


def merge_items(existing: List[Dict[str, object]], new_items: List[Dict[str, object]]):
	by_id = {item.get("id"): item for item in existing}
	for item in new_items:
		by_id[item.get("id")] = item
	return list(by_id.values())


def iter_problem_ids(args) -> Iterable[int]:
	if args.ids:
		for pid in args.ids:
			yield int(pid)
	if args.range:
		start, end = args.range
		for pid in range(int(start), int(end) + 1):
			yield pid
	if args.workbooks:
		for url in WORKBOOK_URLS:
			print(f"[*] Fetching workbook: {url}")
			try:
				pids = fetch_workbook_problem_ids(url)
				print(f"[*] Found {len(pids)} problems in workbook")
				for pid in pids:
					yield pid
			except Exception as e:
				print(f"[!] Failed to fetch workbook {url}: {e}")


def main():
	parser = argparse.ArgumentParser(description="Crawl Baekjoon and update problems_seed.json")
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument("--ids", nargs="+", type=int, help="Explicit problem IDs, e.g., 9663 15686")
	group.add_argument("--range", nargs=2, type=int, metavar=("START", "END"), help="Inclusive range, e.g., 1000 1010")
	group.add_argument("--workbooks", action="store_true", help="Crawl problems from WORKBOOK_URLS list")
	args = parser.parse_args()

	pids = list(iter_problem_ids(args))
	if not pids:
		parser.error("Provide --ids or --range")

	collected = []
	for pid in pids:
		try:
			print(f"[+] Fetching {pid}")
			collected.append(build_item(pid))
		except Exception as e:
			print(f"[!] Skip {pid}: {e}")

	existing = load_existing()
	merged = merge_items(existing, collected)
	save_seed(merged)
	print(f"Saved {len(merged)} items to {SEED_PATH}")


if __name__ == "__main__":
	main()
