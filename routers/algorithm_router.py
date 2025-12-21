from fastapi import APIRouter, HTTPException
import schemas
from services.Algorithm.hint_bot import analyze_problem

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
