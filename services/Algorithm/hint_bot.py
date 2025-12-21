"""알고리즘 문제 유사도 검색 + 소크라테스식 힌트 생성 모듈."""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import List, Dict

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
MODEL_NAME = "all-MiniLM-L6-v2"

_embedding_model = SentenceTransformer(MODEL_NAME)


def _build_text_blob(item: Dict[str, str]) -> str:
    tags = " ".join(item.get("tags", []))
    return (
        f"{item.get('title', '')}. "
        f"{item.get('statement', '')} "
        f"tags: {tags}. "
        f"solution: {item.get('solution_outline', '')}"
    )


@lru_cache(maxsize=1)
def _load_corpus() -> List[Dict[str, str]]:
    data_path = BASE_DIR / "problems_seed.json"
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _get_corpus_embeddings() -> tuple[List[Dict[str, str]], np.ndarray]:
    corpus = _load_corpus()
    blobs = [_build_text_blob(item) for item in corpus]
    embs = _embedding_model.encode(blobs, normalize_embeddings=True)
    return corpus, np.array(embs, dtype=np.float32)


def _get_openai_client() -> OpenAI | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def search_similar_problems(statement: str, top_k: int = 3) -> List[Dict[str, str]]:
    """문제 지문(statement)과 코퍼스 간 코사인 유사도 Top-K 반환."""
    if top_k <= 0:
        top_k = 3

    corpus, embs = _get_corpus_embeddings()
    query_emb = _embedding_model.encode([statement], normalize_embeddings=True)[0]

    sims = np.dot(embs, query_emb)
    sorted_idx = np.argsort(-sims)

    results: List[Dict[str, str]] = []
    for idx in sorted_idx[: min(top_k, len(corpus))]:
        item = corpus[int(idx)]
        sim = float(sims[int(idx)])
        results.append(
            {
                "id": item.get("id", str(idx)),
                "title": item.get("title", ""),
                "source": item.get("source", ""),
                "url": item.get("url"),
                "tags": item.get("tags", []),
                "solution_outline": item.get("solution_outline", ""),
                "similarity": round(sim, 4),
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
