# File: fastAPI/__init__.py
"""
fastAPI package exports.

This module re-exports convenient utilities used across the project so that
agent modules (and tests) can import common helpers via `from fastAPI import ...`.

All heavy imports are wrapped in lazy accessors to prevent circular import
problems with team_agents.
"""
from __future__ import annotations

import importlib
from fastAPI.main import app as fastapi_app

__all__ = [
    # utils
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
    # graph
    "hunt_graph",
    "HuntState",
    # app
    "fastapi_app",
]


# ----------------------
# Lazy loader helper
# ----------------------
class _LazyAttr:
    def __init__(self, module: str, attr: str):
        self._module = module
        self._attr = attr

    def _load(self):
        mod = importlib.import_module(self._module)
        return getattr(mod, self._attr)

    def __getattr__(self, item):
        return getattr(self._load(), item)

    def __call__(self, *args, **kwargs):
        return self._load()(*args, **kwargs)

    def __repr__(self):
        return f"<lazy {self._module}.{self._attr}>"


# ----------------------
# Lazy utils
# ----------------------
cache = _LazyAttr("fastAPI.utils", "cache")
metrics = _LazyAttr("fastAPI.utils", "metrics")
safe_get = _LazyAttr("fastAPI.utils", "safe_get")
to_json_safe = _LazyAttr("fastAPI.utils", "to_json_safe")
get_config = _LazyAttr("fastAPI.utils", "get_config")
safe_ask_llm = _LazyAttr("fastAPI.utils", "safe_ask_llm")
embedder = _LazyAttr("fastAPI.utils", "embedder")
fetch_feed = _LazyAttr("fastAPI.utils", "fetch_feed")
run_query = _LazyAttr("fastAPI.utils", "run_query")
perform_action = _LazyAttr("fastAPI.utils", "perform_action")

# ----------------------
# Lazy graph
# ----------------------
hunt_graph = _LazyAttr("team_agents.core.graph", "hunt_graph")
HuntState = _LazyAttr("team_agents.core.graph", "HuntState")
