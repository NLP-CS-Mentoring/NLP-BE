from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import List, Dict

import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_PATH = BASE_DIR / "problems_seed_flattened.json"
CHROMA_PATH = Path(os.getenv("CHROMA_PATH") or (BASE_DIR / "chroma_db"))
COLLECTION_NAME = "algo_problems"
MODEL_NAME = "all-MiniLM-L6-v2"

_embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
	model_name=MODEL_NAME
)


def _build_text_blob(item: Dict[str, str]) -> str:
    tags = " ".join(item.get("tags", []))
    return (
        f"{item.get('title', '')}. "
        f"{item.get('statement', '')} "
        f"tags: {tags}. "
        f"solution: {item.get('solution_outline', '')}"
    )


def _get_data_path() -> Path:
    env_path = os.getenv("PROBLEMS_PATH")
    return Path(env_path) if env_path else DEFAULT_DATA_PATH


@lru_cache(maxsize=1)
def _load_corpus() -> List[Dict[str, str]]:
    data_path = _get_data_path()
    if not data_path.exists():
        raise FileNotFoundError(f"corpus file not found: {data_path}")
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_openai_client() -> OpenAI | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


@lru_cache(maxsize=1)
def _get_client() -> chromadb.ClientAPI:
	CHROMA_PATH.mkdir(parents=True, exist_ok=True)
	return chromadb.PersistentClient(path=str(CHROMA_PATH))


def _get_collection():
	client = _get_client()
	return client.get_or_create_collection(
		name=COLLECTION_NAME,
		embedding_function=_embedding_fn,
		metadata={"hnsw:space": "cosine"},
	)


def _rebuild_collection(corpus: List[Dict[str, str]]):
	client = _get_client()
	try:
		client.delete_collection(COLLECTION_NAME)
	except Exception:
		pass
	col = _get_collection()
	ids = [item.get("id", str(i)) for i, item in enumerate(corpus)]
	docs = [_build_text_blob(item) for item in corpus]
	metas = []
	for i, item in enumerate(corpus):
		raw_tags = item.get("tags", [])
		tags_str = ", ".join(raw_tags) if isinstance(raw_tags, list) else str(raw_tags)
		metas.append(
			{
				"id": ids[i],
				"title": item.get("title", ""),
				"source": item.get("source", ""),
				"url": item.get("url"),
				"tags": tags_str,
				"solution_outline": item.get("solution_outline", ""),
			}
		)
	if docs:
		col.add(ids=ids, documents=docs, metadatas=metas)


def ensure_collection():
	corpus = _load_corpus()
	col = _get_collection()
	# 간단한 개수 불일치 시 재빌드
	if col.count() != len(corpus):
		_rebuild_collection(corpus)
	return col


def search_similar_problems(statement: str, top_k: int = 3) -> List[Dict[str, str]]:
	"""문제 지문(statement)과 코퍼스 간 코사인 유사도 Top-K 반환."""
	if top_k <= 0:
		top_k = 3

	col = ensure_collection()
	res = col.query(query_texts=[statement], n_results=top_k)
	metas = res.get("metadatas", [[]])[0]
	dists = res.get("distances", [[]])[0] if res.get("distances") else []
	results: List[Dict[str, str]] = []
	for i, m in enumerate(metas or []):
		dist = float(dists[i]) if i < len(dists) else 1.0
		sim = round(1.0 - dist, 4)
		raw_tags = m.get("tags", [])
		if isinstance(raw_tags, str):
			tags_list = [t.strip() for t in raw_tags.split(",") if t.strip()]
		elif isinstance(raw_tags, list):
			tags_list = raw_tags
		else:
			tags_list = []
		results.append(
			{
				"id": m.get("id", ""),
				"title": m.get("title", ""),
				"source": m.get("source", ""),
				"url": m.get("url"),
				"tags": tags_list,
				"solution_outline": m.get("solution_outline", ""),
				"similarity": sim,
			}
		)
	return results


_HINT_SYSTEM_PROMPT = """
You are a calm algorithm mentor. Speak Korean. Offer Socratic hints, not full solutions.
Guidelines:
- Summarize the user's problem briefly.
- Refer to the retrieved similar problems only as inspiration; do not give their full answers.
- Point out potential algorithmic approach (e.g., DFS/backtracking, DP, two-pointer, parametric search) with 2~4 bullet hints.
- Emphasize time/space complexity considerations.
- If user input is vague, ask for missing details (constraints, input size, edge cases).
- NEVER paste full code or final answers.
""".strip()


def _build_context(similar: List[Dict[str, str]]) -> str:
    if not similar:
        return "(no similar problems)"
    lines = []
    for s in similar:
        tags = ", ".join(s.get("tags", []))
        lines.append(
            f"- {s.get('title')} [{s.get('source')}] (tags: {tags}) :: {s.get('solution_outline')}"
        )
    return "\n".join(lines)


def generate_hint(statement: str, similar: List[Dict[str, str]]) -> str:
    client = _get_openai_client()
    context = _build_context(similar)

    if not client:
        # OpenAI 키가 없을 때의 안전한 폴백
        if not similar:
            return "유사 문제를 찾지 못했어요. 입력을 조금 더 구체적으로 적어주면 힌트를 만들 수 있어요 (입력 크기, 조건 등)."

        top = similar[0]
        tag_txt = ", ".join(top.get("tags", []))
        return (
            f"가장 비슷한 문제는 {top.get('title')} ({top.get('source')}) 입니다. "
            f"주요 접근법은 {tag_txt} 입니다. 입력 크기를 다시 확인하고, "
            f"해당 기법으로 시간복잡도가 통과되는지 계산해보세요. "
            f"기본 아이디어를 의사코드로 적어본 뒤, 최악/평균 케이스를 점검해보면 좋아요."
        )

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.4,
        messages=[
            {"role": "system", "content": _HINT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "[문제]\n" + statement + "\n\n" + "[유사 문제]\n" + context
                ),
            },
        ],
    )

    return completion.choices[0].message.content.strip()


def analyze_problem(statement: str, top_k: int = 3) -> Dict[str, object]:
    similar = search_similar_problems(statement, top_k=top_k)
    hint = generate_hint(statement, similar)
    return {"similar": similar, "hint": hint}


def refresh_corpus(new_path: str | None = None) -> Path:
	target_path = Path(new_path) if new_path else _get_data_path()
	if not target_path.exists():
		raise FileNotFoundError(f"corpus file not found: {target_path}")
	os.environ["PROBLEMS_PATH"] = str(target_path)
	_load_corpus.cache_clear()
	_get_client.cache_clear()
	ensure_collection.cache_clear()
	corpus = _load_corpus()
	_rebuild_collection(corpus)
	return target_path
