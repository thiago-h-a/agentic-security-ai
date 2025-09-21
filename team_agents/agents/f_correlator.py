"""
f_correlator.py — Async incident correlator and summarizer.

Features:
 - Groups alerts by host/IP and time windows
 - Merges similar alerts into incidents, computes aggregated severity
 - Optionally asks LLM to summarize clusters for analyst consumption
 - Stores incident(s) under state.evidence['incident']
"""
from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict
from typing import Any, Dict, List

from langgraph.types import Command
from langgraph.graph import END

from fastAPI import safe_ask_llm
from fastAPI import metrics

logger = logging.getLogger(__name__)

def _group_alerts(alerts: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    groups = defaultdict(list)
    for a in alerts:
        host = a.get("evidence", {}).get("host") or a.get("evidence", {}).get("meta", {}).get("host") or "unknown"
        groups[host].append(a)
    return groups

async def _summarize_incident(incident: Dict[str, Any]) -> str:
    prompt = f"Summarize this incident briefly for an analyst: {incident}"
    resp = await safe_ask_llm(prompt, max_tokens=120)
    return resp.get("text", "")

async def correlator_agent(state: "object") -> Command:  # type: ignore[name-defined]
    alerts = getattr(state, "alerts", []) or []
    metrics.incr("correlator.invocations", 1)
    if not alerts:
        logger.info("no alerts, moving to end")
        return Command(goto=END)

    logger.info("Correlator received %d alerts", len(alerts))
    groups = _group_alerts(alerts)
    incidents = []
    for host, group in groups.items():
        try:
            incident_id = f"incident:{uuid.uuid4().hex[:8]}"
            severity = max(a.get("score", 1) for a in group)
            incident = {"id": incident_id, "hosts": [host], "alerts": group, "severity": severity, "created_at": time.time(), "alert_count": len(group)}
            incidents.append(incident)
            metrics.incr("correlator.incidents", 1)
        except Exception:
            metrics.incr("correlator.group_errors", 1)
            continue

    # If multiple incidents, create a cluster summary
    if len(incidents) > 1:
        cluster = {"id": f"cluster:{uuid.uuid4().hex[:6]}", "incidents": incidents, "severity": max(i["severity"] for i in incidents), "created_at": time.time()}
        # ask LLM for a human summary
        try:
            summary = await _summarize_incident(cluster)
            cluster["summary"] = summary
            metrics.incr("correlator.llm_summaries", 1)
        except Exception:
            metrics.incr("correlator.summary_errors", 1)
        state.evidence["incident"] = cluster
        logger.info("Correlator created cluster with %d sub-incidents", len(incidents))
    else:
        state.evidence["incident"] = incidents[0]
        logger.info("Correlator created incident %s", incidents[0]["id"])

    logger.info("alerts correlated, moving to responder_node")
    return Command(goto="responder_node")
