# fastAPI/main.py
"""
FastAPI fastAPI exposing endpoints to run the SecOps hunt pipeline.

Endpoints:
 - POST /run   -> run a hunt with provided messages (list of {"event": ...})
 - GET  /ping  -> simple health check
 - GET  /demo  -> infinite stream of demo_ai cases
"""
from __future__ import annotations

import logging
import random
import asyncio
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from team_agents.core.graph import hunt_graph, HuntState

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


# --- Demo AI streaming ---
COLLECTOR_OUTCOMES = [
    "Normalized 2 SMB events from workstation-12",
    "Collected 3 login anomalies from web01",
    "Parsed 1 suspicious PowerShell execution",
    "No suspicious events found in current logs",
]

INTEL_OUTCOMES = [
    "Matched IP 203.0.113.77 with known C2 infrastructure",
    "Enriched PowerShell command with MITRE ATT&CK T1059.001",
    "Domain suspicious.example.com linked to phishing campaign",
    "No CTI match found for given evidence",
]

HYPOTHESIS_OUTCOMES = [
    "Possible lateral movement via SMB",
    "Potential exfiltration from db02",
    "Suspicion of ransomware on fileserver-01",
    "Unlikely benign scheduled task",
]

QUERY_BUILDER_OUTCOMES = [
    "Compiled query: FROM logs WHERE event_type='SMB' AND failed_logins > 5",
    "Compiled query: FROM dns WHERE domain='suspicious.example.com'",
    "Compiled query: FROM process WHERE command LIKE '%powershell.exe -enc%'",
    "Compiled query: FROM auth WHERE country NOT IN ['US','CA']",
]

DETECTOR_OUTCOMES = [
    "Alert: Multiple failed logins detected on SSH",
    "Alert: Suspicious outbound DNS spike",
    "Alert: Registry persistence created",
    "No alerts detected",
]

CORRELATOR_OUTCOMES = [
    "Correlated SSH brute force with MFA bypass attempt",
    "Correlated DNS exfiltration with PowerShell execution",
    "Single alert only, no correlation",
    "No alerts to correlate",
]

RESPONDER_OUTCOMES = [
    "Isolated workstation-22 from network",
    "Disabled compromised account db02-user",
    "Blocked outbound traffic to 203.0.113.77",
    "No response actions taken",
]


async def demo_streamer():
    case_id = 1
    while True:
        yield f"\n=== Running Case {case_id} ===\n"
        steps = [
            ("collector_node", random.choice(COLLECTOR_OUTCOMES)),
            ("intel_agent", random.choice(INTEL_OUTCOMES)),
            ("hypothesis_agent", random.choice(HYPOTHESIS_OUTCOMES)),
            ("query_builder_agent", random.choice(QUERY_BUILDER_OUTCOMES)),
            ("detector_node", random.choice(DETECTOR_OUTCOMES)),
            ("correlator_node", random.choice(CORRELATOR_OUTCOMES)),
            ("responder_node", random.choice(RESPONDER_OUTCOMES)),
        ]
        for step, outcome in steps:
            await asyncio.sleep(0.6)
            yield f"[{step}] {outcome}\n"
            if "No" in outcome or "Unlikely" in outcome:
                break
        yield f"=== Final State for Case {case_id}: {step} ===\n"
        case_id += 1
        await asyncio.sleep(1)


@app.get("/demo")
async def demo_endpoint():
    """
    Infinite stream of demo_ai cases.
    Each refresh restarts counting from Case 1.
    """
    return StreamingResponse(demo_streamer(), media_type="text/plain")


# Allow running directly for development (uvicorn recommended for production)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("fastAPI.main:app", host="0.0.0.0", port=8000, reload=False)
