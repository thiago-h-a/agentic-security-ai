"""
d_query_builder.py — Async query compilation and safety checks.

Features:
 - Templating with parameter substitution
 - Basic safety filtering to prevent dangerous tokens
 - Validation of ESQL structure and enforcement of limits
 - Emits compiled query objects to state.evidence['queries']
"""
from __future__ import annotations

import logging
import re
import time
from typing import Any, Dict

from langgraph.types import Command

from pydantic import BaseModel, Field, ValidationError

from app import get_config
from app import metrics

logger = logging.getLogger(__name__)

_PLACEHOLDER_RE = re.compile(r"\{\{(?P<name>[\w_]+)\}\}")

class CompiledQuery(BaseModel):
    id: str = Field(...)
    query: str = Field(...)
    params: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)

def _render(template: str, params: Dict[str, Any]) -> str:
    def _r(m):
        name = m.group("name")
        v = params.get(name, f"<{name}>")
        return str(v)
    return _PLACEHOLDER_RE.sub(_r, template)

def _validate_query(q: str) -> bool:
    # Basic checks: FROM + WHERE and no forbidden tokens
    if "FROM" not in q.upper() or "WHERE" not in q.upper():
        return False
    forbidden = [";", "DROP", "DELETE", "--"]
    for t in forbidden:
        if t in q.upper():
            return False
    if len(q) > 4000:
        return False
    return True

async def query_builder_agent(state: "object") -> Command:  # type: ignore[name-defined]
    start = time.time()
    hyps = state.evidence.get("hypotheses", []) or []
    limit = int(get_config("detector.esql_limit") or 1000)
    compiled = []
    metrics.incr("query_builder.invocations", 1)
    for h in hyps:
        try:
            template = "FROM logs WHERE {{query}} | limit {{limit}}"
            params = {"query": h.get("query"), "limit": limit}
            rendered = _render(template, params)
            if not _validate_query(rendered):
                metrics.incr("query_builder.invalid", 1)
                logger.warning("Invalid or unsafe query skipped: %s", rendered)
                continue
            cq = CompiledQuery(id=h.get("id") or f"q_{int(time.time()*1000)}", query=rendered, params=params)
            compiled.append(cq)
            metrics.incr("query_builder.compiled", 1)
        except ValidationError:
            metrics.incr("query_builder.validation_errors", 1)
            continue
    state.evidence["queries"] = compiled
    elapsed = time.time() - start
    metrics.timing("query_builder.duration_seconds", elapsed)
    logger.info("Query builder produced %d compiled queries, moving to detector_node", len(compiled))
    return Command(goto="detector_node")
