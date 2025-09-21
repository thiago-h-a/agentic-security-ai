"""
config.py — agent-level configuration helpers.

This module centralizes per-agent configuration and environment-driven
settings so team_agents can behave differently in staging/production.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

DEFAULTS: Dict[str, Any] = {
    "collector.batch_size": 500,
    "collector.max_retries": 3,
    "intel.cache_ttl_seconds": 300,
    "detector.esql_limit": 1000,
    "responder.soar_action": "isolate_host",
    "correlator.merge_threshold": 2,
}

def get_config(key: str, default: Optional[Any] = None) -> Any:
    env_key = key.upper().replace(".", "_")
    if env_key in os.environ:
        val = os.environ[env_key]
        # attempt to cast booleans/ints if possible
        if val.lower() in ("true", "false"):
            return val.lower() == "true"
        try:
            return int(val)
        except Exception:
            return val
    return DEFAULTS.get(key, default)
