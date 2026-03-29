# reasoning_api.py
import traceback

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from orchestrator import run_neuro_adaptive_engine

app = FastAPI(title="Unicetra Semantic Engine API")


class QueryPayload(BaseModel):
    question: str
    regulation: str = "both"
    max_hops: int = 3


@app.get("/health")
async def check_health():
    return {"status": "operational"}


@app.post("/api/reason")
async def execute_reasoning(request: QueryPayload):
    try:
        # Trigger the primary analytical loop
        execution_output = run_neuro_adaptive_engine(request.question)

        # Standardize schema output
        if "metrics" not in execution_output:
            execution_output["metrics"] = {}

        return execution_output

    except Exception as err:
        print(f"[!] Server Exception: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(err)) from err