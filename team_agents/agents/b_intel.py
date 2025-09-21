"""
b_intel.py — Expanded async CTI enrichment.

Features:
 - Cached CTI feed with TTL using team_agents.utils.SimpleCache
 - Fast approximate matching using substring checks and naive embedding similarity
 - Optional LLM-assisted enrichment for high-risk hits
 - Stores enriched events under state.evidence['enriched']
"""
from __future__ import annotations

import asyncio
import logging
import math
import time
from typing import Any, Dict, List, Sequence

from langgraph.types import Command

from fastAPI import cache, metrics, to_json_safe
from fastAPI import get_config
from fastAPI import embedder, safe_ask_llm
from fastAPI import fetch_feed  # uses existing tools module

logger = logging.getLogger(__name__)

def _approx_similarity(a: list[float], b: list[float]) -> float:
    # cosine-like approximation for demo
    if not a or not b:
        return 0.0
    num = sum(x * y for x, y in zip(a, b))
    denom = math.sqrt(sum(x * x for x in a) * sum(y * y for y in b))
    return num / denom if denom else 0.0

async def _cached_feed(ttl: int = 300) -> List[Dict[str, Any]]:
    cached = cache.get("cti_feed")
    now = time.time()
    if cached and cache.get("cti_feed_ts") and now - cache.get("cti_feed_ts", 0) < ttl:
        return cached
    # fetch (sync function wrapped in threadpool)
    loop = asyncio.get_event_loop()
    raw = await loop.run_in_executor(None, fetch_feed)
    # simple normalisation of items to dicts (pydantic objects may be returned)
    items: List[Dict[str, Any]] = []
    for it in raw:
        try:
            items.append(it.dict() if hasattr(it, "dict") else dict(it))
        except Exception:
            continue
    cache.set("cti_feed", items, ttl=ttl)
    cache.set("cti_feed_ts", now, ttl=ttl)
    metrics.incr("intel.feed_refreshed", 1)
    return items

async def _enrich_event(evt: Dict[str, Any], feed: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    # quick exact match
    for item in feed:
        if item.get("attributes", {}).get("value") and (item["attributes"]["value"] == evt.get("host") or item["attributes"]["value"] == evt.get("meta", {}).get("ip")):
            # annotate with CTI item and compute confidence via embedding similarity
            evt = dict(evt)
            evt["indicator_match"] = True
            evt["indicator"] = item
            base_emb = embedder(str(evt.get("host") or evt.get("meta", {})))
            item_emb = embedder(str(item.get("attributes", {}).get("value", "")))
            evt["indicator_confidence"] = _approx_similarity(base_emb, item_emb)
            metrics.incr("intel.hits_exact", 1)
            # optionally, ask the LLM for a short rationale for high-confidence matches
            if evt["indicator_confidence"] > 0.5:
                prompt = f"Provide a one-line rationale for why this event matches CTI: event={to_json_safe(evt)[:300]}"
                resp = await safe_ask_llm(prompt, max_tokens=80)
                evt["indicator_rationale"] = resp.get("text")
            return evt
    # fuzzy pass: substring matching on meta values
    for item in feed:
        val = item.get("attributes", {}).get("value", "")
        if val and (val in (evt.get("host") or "") or val in str(evt.get("meta", {}))):
            evt = dict(evt)
            evt["indicator_match"] = True
            evt["indicator"] = item
            evt["indicator_confidence"] = 0.35
            metrics.incr("intel.hits_fuzzy", 1)
            return evt
    # no hit
    return evt

async def intel_agent(state: "object") -> Command:  # type: ignore[name-defined]
    start = time.time()
    raw = state.evidence.get("raw", []) or []
    metrics.incr("intel.invocations", 1)
    ttl = int(get_config("intel.cache_ttl_seconds") or 300)
    feed = await _cached_feed(ttl=ttl)
    enriched: List[Dict[str, Any]] = []
    for evt in raw:
        try:
            enriched_evt = await _enrich_event(evt, feed)
            enriched.append(enriched_evt)
        except Exception as exc:
            logger.exception("Enrichment failed for event %s: %s", evt.get("id"), exc)
            metrics.incr("intel.errors", 1)
            enriched.append(evt)
    state.evidence["enriched"] = enriched
    elapsed = time.time() - start
    metrics.timing("intel.duration_seconds", elapsed)
    logger.info("Intel enriched %d events (duration=%.3fs), moving to hypothesis_agent", len(enriched), elapsed)
    return Command(goto="hypothesis_agent")
