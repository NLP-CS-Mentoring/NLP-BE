from .prompts import question_prompt
from .openai_client import responses_json_schema  # <--- githubInterview를 점(.)으로 변경

QUESTION_SCHEMA = {
    "name": "repo_interview_question",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "question": {"type": "string"},
            "rubric": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 8},
            "expected_answer": {"type": "string"},
        },
        "required": ["question", "rubric", "expected_answer"],
    },
    "strict": True,
}

def generate_question(repo_context: str, difficulty: str) -> dict:
    content = question_prompt(difficulty) + "\n\n[REPO CONTEXT]\n" + repo_context
    return responses_json_schema("gpt-5.1", content, QUESTION_SCHEMA)