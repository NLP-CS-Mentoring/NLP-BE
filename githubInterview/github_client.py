import os
import re
import requests
from fastapi import HTTPException

def parse_repo(repo_url: str) -> tuple[str, str]:
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)(?:/.*)?$", repo_url.strip())
    if not m:
        raise HTTPException(400, "GitHub repository URL 형식이 아닙니다.")
    owner = m.group(1)
    repo = m.group(2).replace(".git", "")
    return owner, repo

def gh_get_json(url: str, token: str | None = None, return_headers: bool = False):
    # token이 주어지지 않으면 환경변수 `GITHUB_TOKEN`을 사용합니다.
    token = token or os.getenv("GITHUB_TOKEN")

    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    r = requests.get(url, headers=headers, timeout=10)

    if r.status_code == 404:
        raise HTTPException(404, "존재하지 않는 레포입니다.")

    if r.status_code == 403:
        raise HTTPException(
            403,
            "GitHub API 요청 제한에 걸렸습니다. 잠시 후 다시 시도하세요."
        )

    if not r.ok:
        raise HTTPException(r.status_code, "GitHub API 오류")

    if return_headers:
        return r.json(), r.headers

    return r.json()


def get_rate_limit_remaining(token: str | None = None) -> int:
    """현재 남은 rate limit (core)을 반환합니다. 실패 시 큰 수(1000)를 반환하여 안전하게 동작하도록 합니다."""
    try:
        data = gh_get_json("https://api.github.com/rate_limit", token)
        core = data.get("resources", {}).get("core", {})
        return int(core.get("remaining", 1000))
    except Exception:
        return 1000

def fetch_repo_tree(owner: str, repo: str) -> tuple[str, list[str]]:
    repo_info = gh_get_json(f"https://api.github.com/repos/{owner}/{repo}")
    branch = repo_info.get("default_branch", "main")

    tree = gh_get_json(
        f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    )
    items = tree.get("tree", [])
    paths = [it["path"] for it in items if it.get("type") == "blob"]
    return branch, paths

def fetch_file_text(owner: str, repo: str, path: str, branch: str) -> str:
    meta = gh_get_json(
        f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
    )
    download_url = meta.get("download_url")
    if not download_url:
        return ""
    r = requests.get(download_url, timeout=12)
    return r.text if r.ok else ""