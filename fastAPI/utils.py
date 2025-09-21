# File: fastAPI/utils.py
"""
Compatibility utilities provided at the fastAPI package level so team_agents can import
shared helpers via `from fastAPI import ...`.

This module wraps or re-exports a small, test-friendly set of helpers the team_agents

"""
from __future__ import annotations

from team_agents.agents.lib.utils import cache, metrics, safe_get, to_json_safe
from team_agents.agents.lib.config import get_config
from team_agents.core.llm import safe_ask_llm, embedder
from team_agents.tools.cti_feed import fetch_feed
from team_agents.tools.elastic_esql import run_query
from team_agents.tools.soar_actions import perform_action

__all__ = [
    "cache",
    "metrics",
    "safe_get",
    "to_json_safe",
    "get_config",
    "safe_ask_llm",
    "embedder",
    "fetch_feed",
    "run_query",
    "perform_action",
]
