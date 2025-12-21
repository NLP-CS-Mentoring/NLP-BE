import json
import os
from typing import Optional
from openai import OpenAI


# 지연 초기화용 내부 캐시
_client: Optional[OpenAI] = None


def get_client(api_key: Optional[str] = None) -> OpenAI:
    """OpenAI 클라이언트를 가져옵니다.

    - 우선 내부 캐시된 인스턴스를 반환합니다.
    - 없으면 `api_key` 인수 또는 `OPENAI_API_KEY` 환경변수에서 키를 읽어 생성합니다.
    - 키가 없으면 명확한 에러를 발생시켜 import 시점에서 실패하지 않도록 합니다.
    """
    global _client
    if _client is None:
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError(
                "OPENAI_API_KEY environment variable not set. "
                "Pass api_key to get_client() or set OPENAI_API_KEY."
            )
        _client = OpenAI(api_key=key)
    return _client


def responses_json_schema(model: str, user_content: str, json_schema: dict) -> dict:
    """
    OpenAI Responses API 호출 후, json_schema로 강제된 JSON 결과를 dict로 반환.
    """
    client = get_client()
    # support wrapper { name, schema, ... } or raw JSON Schema dict
    if isinstance(json_schema, dict) and "schema" in json_schema:
        schema_obj = json_schema["schema"]
        name = json_schema.get("name") or "response"
    else:
        schema_obj = json_schema
        name = getattr(json_schema, "get", lambda k, d=None: d)("name", "response")

    res = client.responses.create(
        model=model,
        input=[{"role": "user", "content": user_content}],
        text={
            "format": {
                "type": "json_schema",
                "name": name,
                "schema": schema_obj,
                "json_schema": schema_obj,
            }
        },
    )
    return json.loads(res.output_text)