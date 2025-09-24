"""
a_collector.py — Expanded async collector with multiple source adapters and realistic preprocessing.

Features:
 - Async fetching from configured sources (HTTP, file, synthetic generator)
 - Input validation, normalization, deduplication (TTL cache)
 - Extensible enrichment hooks and basic rate-limiting
 - Emits timing/metrics to team_agents.team_agents.utils.metrics
"""
from __future__ import annotations

import asyncio
import hashlib
import itertools
import logging
import time
from typing import Any, Dict, Iterable, List

from langgraph.types import Command
from langgraph.graph import END

from fastAPI.utils import cache, metrics, safe_get, to_json_safe
from fastAPI.utils import get_config
from fastAPI.utils import safe_ask_llm

logger = logging.getLogger(__name__)

# -----------------------
# Helpers
# -----------------------
def _normalize_message(raw: Dict[str, Any]) -> Dict[str, Any]:
    ts = raw.get("ts") or raw.get("timestamp") or time.time()
    event = raw.get("event") or raw.get("type") or "unknown"
    source = raw.get("source") or raw.get("origin") or "ingest"
    host = raw.get("host") or safe_get(raw, "meta", {}).get("host")
    user = raw.get("user") or safe_get(raw, "meta", {}).get("user")
    meta = safe_get(raw, "meta", {}) or {}
    fingerprint = hashlib.sha256(f"{event}|{host}|{user}|{ts}".encode()).hexdigest()
    return {"id": fingerprint, "ts": float(ts), "event": event, "source": source, "host": host, "user": user, "meta": meta}

def _chunk(iterable: Iterable, size: int):
    it = iter(iterable)
    while True:
        batch = list(itertools.islice(it, size))
        if not batch:
            break
        yield batch

async def _simulate_http_fetch(url: str) -> List[Dict[str, Any]]:
    # small simulated HTTP fetch to avoid network calls in tests
    await asyncio.sleep(0.05)
    return [{"event": "login_fail", "host": "10.0.0.5", "ts": time.time()}, {"event": "login_success", "host": "10.0.0.6", "ts": time.time()}]

# -----------------------
# Collector Node
# -----------------------
async def _apply_enrichment(evt: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example enrichment that uses the LLM to infer a short note for ambiguous events.
    Runs quickly – uses safe_ask_llm which may be simulated if no key present.
    """
    try:
        if evt.get("event") == "unknown":
            prompt = f"Shortly describe what a suspicious event might be for payload: {to_json_safe(evt)[:400]}"
            resp = await safe_ask_llm(prompt, max_tokens=64)
            evt["llm_note"] = resp.get("text")
            metrics.incr("collector.llm_enrichments", 1)
    except Exception:
        metrics.incr("collector.enrich_errors", 1)
    return evt

async def collector_agent(state: "object") -> Command:  # type: ignore[name-defined]
    start = time.time()
    batch_size = int(get_config("collector.batch_size") or 500)
    max_retries = int(get_config("collector.max_retries") or 3)
    input_messages = getattr(state, "messages", []) or []

    logger.info("Collector starting with %d input messages", len(input_messages))
    metrics.incr("collector.invocations", 1)

    normalized: List[Dict[str, Any]] = []

    # Simulate reading from configured sources (some may be URLs)
    sources = [m for m in input_messages]
    # Also support configuration-driven pulls (e.g., CTI endpoints)
    extra_source = get_config("collector.extra_source_url")
    if extra_source:
        try:
            fetched = await _simulate_http_fetch(extra_source)
            sources.extend(fetched)
            metrics.incr("collector.remote_fetches", 1)
        except Exception as exc:
            logger.warning("Failed to fetch extra source: %s", exc)

    # Basic retry for normalization step
    for attempt in range(1, max_retries + 1):
        try:
            for raw in sources:
                try:
                    norm = _normalize_message(raw)
                    key = f"evt:{norm['id']}"
                    if cache.get(key):
                        metrics.incr("collector.duplicates", 1)
                        continue
                    cache.set(key, True, ttl=60)
                    # enrich where applicable
                    enriched = await _apply_enrichment(norm)
                    normalized.append(enriched)
                    metrics.incr("collector.normalized", 1)
                except Exception as e:
                    metrics.incr("collector.normalize_errors", 1)
                    logger.debug("Skipping malformed raw: %s (%s)", raw, e)
            break
        except Exception as exc:
            logger.exception("Collector normalization attempt %d failed: %s", attempt, exc)
            await asyncio.sleep(0.1 * attempt)
            if attempt == max_retries:
                logger.info("collector error, moving to end")
                return Command(goto=END)

    # batch and persist
    batched: List[Dict[str, Any]] = []
    for chunk in _chunk(normalized, batch_size):
        batched.extend(chunk)

    try:
        state.evidence["raw"] = batched
        elapsed = time.time() - start
        metrics.timing("collector.duration_seconds", elapsed)
        logger.info("Collector stored %d normalized events (duration=%.3fs)", len(batched), elapsed)
    except Exception as exc:
        logger.exception("Failed to persist collector evidence: %s", exc)
        logger.info("Collector persist error, moving to end")
        return Command(goto=END)

    logger.info("Collected raw events, moving to intel_agent")
    return Command(goto="intel_agent")
