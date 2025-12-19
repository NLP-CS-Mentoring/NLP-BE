import re
from .github_client import fetch_file_text, fetch_repo_tree, get_rate_limit_remaining

def choose_important_paths(paths: list[str], limit: int = 10) -> list[str]:
    patterns = [
        r"^README\.md$",
        r"^pyproject\.toml$|^requirements\.txt$|^Pipfile$",
        r"docker-compose\.ya?ml$|Dockerfile$",
        r"(?:^|/)main\.py$|(?:^|/)app\.py$",
        r"(?:^|/)(router|routes|api)/",
        r"(?:^|/)(service|usecase|domain)/",
        r"(?:^|/)(auth|security|jwt|oauth)/",
        r"(?:^|/)(db|database|models)/",
        r"(?:^|/)config|settings",
        r"(?:^|/)test",
    ]

    scored = []
    for p in paths:
        score = 0
        for i, pat in enumerate(patterns):
            if re.search(pat, p, re.IGNORECASE):
                score += (len(patterns) - i)
        if score > 0:
            scored.append((score, p))

    scored.sort(reverse=True)
    picked = [p for _, p in scored[:limit]]
    return picked or ["README.md"]

def build_repo_context(owner: str, repo: str) -> tuple[str, str]:
    branch, all_paths = fetch_repo_tree(owner, repo)
    important = choose_important_paths(all_paths, limit=10)

    # 남은 rate limit에 맞춰 읽을 파일 수를 제한합니다.
    remaining = get_rate_limit_remaining()
    # 안전 마진: 다른 내부 호출을 위해 몇 건 확보합니다.
    safe_reserve = 3
    allowed = max(0, remaining - safe_reserve)
    if allowed == 0:
        # 한도가 없으면 README만 읽도록 최소화
        important = [p for p in important if p.lower().endswith('readme.md')][:1] or []
    else:
        important = important[:allowed]

    chunks = []
    for path in important:
        text = fetch_file_text(owner, repo, path, branch)
        if not text.strip():
            continue
        if len(text) > 12000:
            text = text[:12000] + "\n\n...[truncated]"
        chunks.append(f"\n### FILE: {path}\n{text}\n")

    context = "\n".join(chunks)
    if len(context) > 45000:
        context = context[:45000] + "\n\n...[context truncated]"
    return context, branch