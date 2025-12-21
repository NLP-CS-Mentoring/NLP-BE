from fastapi import APIRouter, HTTPException, Query
import schemas
from services.Algorithm.hint_bot import analyze_problem, refresh_corpus

router = APIRouter(prefix="/algo-helper", tags=["Algorithm Helper"])


@router.post("/hint", response_model=schemas.AlgorithmHintResponse)
def get_algorithm_hint(req: schemas.AlgorithmProblemRequest):
    statement = (req.statement or "").strip()
    if not statement:
        raise HTTPException(status_code=400, detail="problem statement is empty")

    try:
        return analyze_problem(statement, top_k=req.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
def refresh_algorithm_corpus(file_path: str | None = Query(None, description="Absolute path to crawled corpus JSON")):
    try:
        data_path = refresh_corpus(file_path)
        return {"status": "ok", "data_path": str(data_path)}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
