"""
FastAPI app exposing endpoints to run the SecOps hunt pipeline.

Endpoints:
 - POST /run   -> run a hunt with provided messages (list of {"event": ...})
 - GET  /ping  -> simple health check
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app import hunt_graph, HuntState

logger = logging.getLogger("team_agents.api")
app = FastAPI(title="SecOps Graph API", version="0.1.0")

class RunRequest(BaseModel):
    messages: List[Dict[str, Any]] = []

class RunResponse(BaseModel):
    alerts: List[Dict[str, Any]] = []
    story: Dict[str, Any] | None = None

@app.get("/ping")
def ping() -> Dict[str, str]:
    return {"status": "ok"}

@app.post("/run", response_model=RunResponse)
def run_hunt(req: RunRequest):
    """
    Invoke the compiled LangGraph pipeline synchronously using the
    supplied messages as initial state. Returns alerts and story.
    """
    try:
        state = HuntState(messages=req.messages)
        result = hunt_graph.invoke(state)
        return RunResponse(alerts=result.alerts or [], story=result.story)
    except Exception as exc:
        logger.exception("Hunt run failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

# Allow running directly for development (uvicorn recommended for production)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("team_agents.api:app", host="0.0.0.0", port=8000, reload=False)
