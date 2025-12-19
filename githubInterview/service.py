from fastapi import HTTPException
from .schemas import QuestionReq, GradeReq
from .github_client import parse_repo
from .context_builder import build_repo_context
from .question_generator import generate_question
from .answer_grader import grade
from .session_store import save_session, get_session

def create_interview_question(req: QuestionReq) -> dict:
    owner, repo = parse_repo(req.repo_url)
    context, branch = build_repo_context(owner, repo)

    if not context.strip():
        raise HTTPException(400, "레포에서 읽을 텍스트(README/코드)를 확보하지 못했습니다.")

    q_pack = generate_question(context, req.difficulty)

    session_id = save_session(
        question_pack=q_pack,
        meta={"repo_url": req.repo_url, "owner": owner, "repo": repo, "branch": branch}
    )

    return {"session_id": session_id, "question": q_pack["question"], "rubric": q_pack["rubric"]}

def grade_interview_answer(req: GradeReq) -> dict:
    s = get_session(req.session_id)
    if not s:
        raise HTTPException(404, "session_id를 찾지 못했습니다.")
    return grade(s["question_pack"], req.answer)