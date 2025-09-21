"""
c_hypothesis.py — Async hypothesis generation and ranking.

Features:
 - Aggregates signals from enriched events.
 - Generates candidate hypotheses with support metrics.
 - Uses LLM to refine rationale and optionally produce suggested queries.
 - Outputs ordered hypotheses to state.evidence['hypotheses'].
"""
from __future__ import annotations

import asyncio
import logging
import math
import random
import time
from typing import Any, Dict, List

from langgraph.types import Command

from fastAPI import safe_ask_llm
from fastAPI import metrics, to_json_safe

logger = logging.getLogger(__name__)

def _aggregate(enriched: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {}
    for e in enriched:
        k = e.get("event", "unknown")
        counts[k] = counts.get(k, 0) + 1
        if e.get("indicator_match"):
            counts["indicator_hits"] = counts.get("indicator_hits", 0) + 1
    return counts

def _initial_candidates(signals: Dict[str, int]) -> List[Dict[str, Any]]:
    cand = []
    if signals.get("login_fail", 0) >= 3:
        cand.append({"id": "bruteforce", "query": "event == 'login_fail'", "support": signals.get("login_fail", 0), "severity": 5})
    if signals.get("indicator_hits", 0) >= 1:
        cand.append({"id": "known_ioc", "query": "indicator_match == true", "support": signals.get("indicator_hits", 0), "severity": 4})
    # generic anomaly hypothesis
    cand.append({"id": "anomaly", "query": "derived_severity >= 2", "support": signals.get("login_fail", 0), "severity": 2})
    return cand

async def _refine_hypothesis(hyp: Dict[str, Any]) -> Dict[str, Any]:
    # Use LLM to expand rationale and propose example filters
    try:
        prompt = f"Given hypothesis: {hyp}, propose a concise rationale (one sentence) and an example query snippet."
        resp = await safe_ask_llm(prompt, max_tokens=120)
        hyp = dict(hyp)
        hyp["rationale"] = resp.get("text")
        metrics.incr("hypothesis.llm_refinements", 1)
    except Exception:
        metrics.incr("hypothesis.refine_errors", 1)
    return hyp

async def hypothesis_agent(state: "object") -> Command:  # type: ignore[name-defined]
    start = time.time()
    enriched = state.evidence.get("enriched", []) or []
    metrics.incr("hypothesis.invocations", 1)
    signals = _aggregate(enriched)
    logger.debug("Signals: %s", signals)
    candidates = _initial_candidates(signals)

    # optionally refine with LLM concurrently for speed
    tasks = [asyncio.create_task(_refine_hypothesis(c)) for c in candidates]
    refined = []
    for t in tasks:
        try:
            refined.append(await t)
        except Exception:
            refined.append({})
    # score using severity and support with randomness for tie-break
    for r in refined:
        r["score"] = r.get("severity", 1) * math.log1p(r.get("support", 0) + 1) + random.random() * 0.05
        r["created_at"] = time.time()
    refined_sorted = sorted(refined, key=lambda x: -x.get("score", 0))
    state.evidence["hypotheses"] = refined_sorted
    metrics.incr("hypothesis.generated", len(refined_sorted))
    elapsed = time.time() - start
    metrics.timing("hypothesis.duration_seconds", elapsed)
    logger.info("Hypothesis agent generated %d hypotheses (duration=%.3fs), moving to query_builder_agent", len(refined_sorted), elapsed)
    return Command(goto="query_builder_agent")
