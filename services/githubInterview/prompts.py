def question_prompt(difficulty: str) -> str:
    return f"""
너는 개발팀 기술면접관이다.
아래 레포 컨텍스트(README/핵심 코드 일부)를 근거로 면접 질문 1개를 만들어라.

조건:
- 난이도: {difficulty}
- 질문은 레포에서 관찰 가능한 사실을 기반으로 구체적으로
- 채점이 가능하도록 rubric(채점 포인트)와 expected_answer(모범답안)을 함께 생성
- 출력은 스키마에 맞는 JSON만
- 반드시 JSON만 출력하라. 추가 설명이나 부가 텍스트를 출력하지 마라.
- 출력 길이 제한(응답이 너무 길면 요약하여 작성):
    - `question`: 최대 200자
    - `rubric`: 3~6개 항목, 각 항목 최대 120자
    - `expected_answer`: 최대 700자
    - 출력 예시: {{"question":"...","rubric":["p1","p2"],"expected_answer":"..."}}
""".strip()


def grading_prompt() -> str:
    return """
너는 개발팀의 기술면접 채점자이다.
아래에 주어진 `question`, `rubric`, `expected_answer`, `user_answer`를 바탕으로 채점하라.

조건:
- `rubric`의 항목들을 기준으로 `user_answer`를 채점하고, 각 항목별로 누락된 포인트를 `missing_points`에 배열로 정리하라.
- 최종 판단(`verdict`)은 `correct`, `partial`, `wrong` 중 하나로 반환하라.
- 점수(`score`)는 0~10 정수로 반환하라.
- `feedback`에는 개선 포인트를 친절히 설명하고, `ideal_answer`에는 간단한 모범답안을, `followup_question`에는 추가 질문 한 개를 작성하라.
- 출력은 엄격하게 JSON 스키마에 맞추어 반환하라.
""".strip()