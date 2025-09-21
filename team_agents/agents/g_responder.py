"""
g_responder.py — Async responder that creates narrative and triggers SOAR.

Features:
 - Generates an analyst-facing narrative using the LLM
 - Invokes SOAR (via tools.soar_actions.perform_action) with retry/backoff
 - Persists action results in state.evidence['soar_result']
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, Optional

from langgraph.types import Command
from langgraph.graph import END

from app import safe_ask_llm
from app import SOARAction, perform_action
from app import get_config
from app import metrics

logger = logging.getLogger(__name__)

async def _generate_story(incident: Dict[str, Any]) -> str:
    prompt = f"Create a concise incident summary for analysts from this structured incident: {incident}"
    resp = await safe_ask_llm(prompt, max_tokens=180)
    return resp.get("text", "")

async def _invoke_soar(action_name: str, params: Dict[str, Any], retries: int = 3) -> Optional[Dict[str, Any]]:
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            # perform_action is sync; run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(None, perform_action, SOARAction(action_name=action_name, parameters=params))
            return {"status": resp.status, "message": getattr(resp, "message", None), "data": getattr(resp, "data", None)}
        except Exception as exc:
            last_exc = exc
            await asyncio.sleep(0.2 * attempt)
            logger.warning("SOAR invocation attempt %d failed: %s", attempt, exc)
    metrics.incr("responder.soar_failed", 1)
    logger.exception("SOAR invocation ultimately failed: %s", last_exc)
    return None

async def responder_agent(state: "object") -> Command:  # type: ignore[name-defined]
    incident = state.evidence.get("incident")
    if not incident:
        logger.info("nothing to respond to, moving to end")
        return Command(goto=END)
    metrics.incr("responder.invocations", 1)
    try:
        story_text = await _generate_story(incident)
        state.story = {"summary": story_text, "generated_at": time.time()}

        action_name = get_config("responder.soar_action") or "isolate_host"
        params = {"incident_id": incident.get("id"), "severity": incident.get("severity")}
        result = await _invoke_soar(action_name, params, retries=3)
        state.evidence["soar_result"] = result
        metrics.incr("responder.soar_calls", 1 if result else 0)
        logger.info("Responder generated story and invoked SOAR (result=%s)", result)
    except Exception as exc:
        logger.exception("Responder failed: %s", exc)
        metrics.incr("responder.errors", 1)
        logger.info("responder error, moving to end")
        return Command(goto=END)
    logger.info("story generated, moving to end")
    return Command(goto=END)
