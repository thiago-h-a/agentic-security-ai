"""
e_detector.py — Async detector capable of running ESQL or scoring events locally.

Features:
 - Executes compiled queries using tools.elastic_esql.run_query (threadpool)
 - Supports fallback to local event inspection
 - Converts results into typed alerts with scoring heuristics
 - Optional LLM scoring for ambiguous events (async)
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Sequence

from langgraph.types import Command
from langgraph.graph import END

from pydantic import BaseModel, Field

from fastAPI import metrics
from fastAPI import safe_ask_llm
from fastAPI import run_query, ESQLQuery

logger = logging.getLogger(__name__)

class Alert(BaseModel):
    id: str = Field(...)
    evidence: Dict[str, Any] = Field(...)
    score: float = Field(default=1.0)
    tags: List[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)

async def _run_compiled_queries(compiled: List[ESQLQuery]) -> List[Dict[str, Any]]:
    rows = []
    loop = asyncio.get_event_loop()
    for q in compiled:
        try:
            # run_query is sync; execute in threadpool
            resp = await loop.run_in_executor(None, run_query, ESQLQuery(query=q.query))
            cols = [c["name"] for c in resp.columns]
            for r in resp.rows:
                rows.append(dict(zip(cols, r)))
            metrics.incr("detector.query_rows", len(resp.rows))
        except Exception as exc:
            metrics.incr("detector.query_errors", 1)
            logger.warning("Query failed: %s ; error=%s", q.query, exc)
            continue
    return rows

def _rows_to_alerts(rows: Sequence[Dict[str, Any]]) -> List[Alert]:
    alerts = []
    for idx, r in enumerate(rows):
        aid = r.get("id") or f"alert_{int(time.time()*1000)}_{idx}"
        score = float(r.get("severity", 1)) + float(r.get("derived_severity", 0))
        tags = []
        if r.get("indicator_match"):
            tags.append("ioc")
        if r.get("event") == "login_fail":
            tags.append("auth.failure")
        alerts.append(Alert(id=aid, evidence=r, score=score, tags=tags))
    return alerts

async def _llm_score_alert(evidence: Dict[str, Any]) -> float:
    # ask LLM for a short risk score suggestion (simulated if offline)
    prompt = f"Given this event evidence, assign a risk score 0-10 and justify briefly: {evidence}"
    resp = await safe_ask_llm(prompt, max_tokens=48)
    try:
        text = resp.get("text", "")
        # parse leading number if present
        first = text.strip().split()[0]
        val = float(first)
        return max(0.0, min(10.0, val))
    except Exception:
        # fallback: minor random scaling
        return float(evidence.get("derived_severity", 0))

async def detector_agent(state: "object") -> Command:  # type: ignore[name-defined]
    start = time.time()
    compiled = state.evidence.get("queries", []) or []
    raw = state.evidence.get("raw", []) or []
    metrics.incr("detector.invocations", 1)

    rows = []
    if compiled:
        logger.info("Detector executing %d compiled queries", len(compiled))
        rows = await _run_compiled_queries(compiled)
    else:
        logger.info("Detector using raw events inspection (%d events)", len(raw))
        rows = raw

    alerts = _rows_to_alerts(rows)
    if not alerts:
        logger.info("Detector found no alerts, moving to end")
        return Command(goto=END)

    # Optionally use LLM to refine scores for top-N alerts
    try:
        top_n = min(3, len(alerts))
        tasks = [asyncio.create_task(_llm_score_alert(a.evidence)) for a in alerts[:top_n]]
        idx = 0
        for t in tasks:
            try:
                new_score = await t
                alerts[idx].score = max(alerts[idx].score, new_score)
            except Exception:
                pass
            idx += 1
        metrics.incr("detector.alerts_emitted", len(alerts))
        state.alerts = [a.dict() for a in alerts]
        logger.info("Detector emitted %d alerts", len(alerts))
    except Exception as exc:
        logger.exception("Detector failed during scoring: %s, moving to end", exc)
        return Command(goto=END)

    elapsed = time.time() - start
    metrics.timing("detector.duration_seconds", elapsed)
    logger.info("anomalies detected, moving to correlator_node")
    return Command(goto="correlator_node", update={"alerts": state.alerts})
