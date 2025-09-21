# File: app/__init__.py
"""
app package exports.

This module re-exports convenient utilities used across the project so that
agent modules (and tests) can import common helpers via `from app import ...`.

It also preserves the previous re-export of the web application and hunt_graph
if those modules are available in the repository.
"""
from __future__ import annotations

from .utils import (  # noqa: F401
    cache,
    metrics,
    safe_get,
    to_json_safe,
    get_config,
    safe_ask_llm,
    embedder,
    fetch_feed,
    run_query,
    perform_action,
)

from team_agents.core.graph import hunt_graph, HuntState
from app.main import app as fastapi_app

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
    "hunt_graph",
    "HuntState",
    "fastapi_app",
]
