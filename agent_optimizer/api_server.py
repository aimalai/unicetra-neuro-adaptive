from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from code_optimizer import CodeREAParser

app = FastAPI(
    title="Occo Coding Agent Optimizer Middleware",
    description="Information-theoretic token compression for enterprise coding agent pipelines.",
    version="1.0.0"
)

class OptimizationRequest(BaseModel):
    files: Dict[str, str]
    focus_keywords: List[str]
    entropy_threshold: float = 2.0

@app.post("/api/v1/optimize-code-context")
async def optimize_code_context(payload: OptimizationRequest):
    try:
        parser = CodeREAParser(target_focus_keywords=payload.focus_keywords)
        result = parser.optimize_repository(payload.files, threshold=payload.entropy_threshold)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)