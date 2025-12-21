import json
from .prompts import grading_prompt
from .openai_client import responses_json_schema

GRADE_SCHEMA = {
    "name": "repo_interview_grade",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "verdict": {"type": "string", "enum": ["correct", "partial", "wrong"]},
            "score": {"type": "integer", "minimum": 0, "maximum": 10},
            "feedback": {"type": "string"},
            "missing_points": {"type": "array", "items": {"type": "string"}},
            "ideal_answer": {"type": "string"},
            "followup_question": {"type": "string"},
        },
        "required": ["verdict", "score", "feedback", "missing_points", "ideal_answer", "followup_question"],
    },
    "strict": True,
}

def grade(question_pack: dict, user_answer: str) -> dict:
    payload = {
        "question": question_pack["question"],
        "rubric": question_pack["rubric"],
        "expected_answer": question_pack["expected_answer"],
        "user_answer": user_answer,
    }

    content = grading_prompt() + "\n\n" + json.dumps(payload, ensure_ascii=False)
    return responses_json_schema(
        model="gpt-5.1",
        user_content=content,
        json_schema=GRADE_SCHEMA
    )