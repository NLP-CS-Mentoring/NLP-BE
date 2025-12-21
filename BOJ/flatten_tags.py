import json
from pathlib import Path

def flatten_tags(doc: dict) -> dict:
    if isinstance(doc.get("tags"), list):
        doc["tags"] = ", ".join(map(str, doc["tags"]))
    return doc

def main(inp: str, outp: str) -> None:
    data = json.loads(Path(inp).read_text())
    if isinstance(data, list):
        data = [flatten_tags(d) for d in data]
    elif isinstance(data, dict):
        data = flatten_tags(data)
    Path(outp).write_text(json.dumps(data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    inp = "./services/Algorithm/problems_seed.json"  # 입력 파일 경로
    outp = "./services/Algorithm/problems_seed_flattened.json"  # 출력 파일 경로
    main(inp, outp)