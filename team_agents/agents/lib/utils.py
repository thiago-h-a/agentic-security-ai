"""
utils.py — utilities used across team_agents.

Contains:
 - simple metrics collector
 - typed helpers for defensive programming
 - JSON-safe serialization helpers
 - in-memory cache wrapper (thread-safe)
"""
from __future__ import annotations

import json
import logging
import threading
import time
from collections import defaultdict
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Simple metrics collector (thread-safe)
class Metrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: Dict[str, int] = defaultdict(int)
        self._timings: Dict[str, float] = defaultdict(float)

    def incr(self, name: str, amount: int = 1) -> None:
        with self._lock:
            self._counters[name] += amount

    def timing(self, name: str, seconds: float) -> None:
        with self._lock:
            self._timings[name] += seconds

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "counters": dict(self._counters),
                "timings": dict(self._timings),
            }

metrics = Metrics()

# Simple thread-safe in-memory cache with TTL
class SimpleCache:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data: Dict[str, Any] = {}
        self._exp: Dict[str, float] = {}

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        with self._lock:
            self._data[key] = value
            self._exp[key] = time.time() + ttl if ttl else float("inf")

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            exp = self._exp.get(key, 0)
            if time.time() > exp:
                # expired
                self._data.pop(key, None)
                self._exp.pop(key, None)
                return default
            return self._data.get(key, default)

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)
            self._exp.pop(key, None)

cache = SimpleCache()

# Defensive helper that attempts to extract keys and provide defaults
def safe_get(dct: dict, key: str, default: Any = None) -> Any:
    try:
        return dct.get(key, default)
    except Exception:
        return default

# JSON serialiser that handles non-serialisable objects gracefully
def to_json_safe(obj: Any, *, indent: int = 2) -> str:
    def default(o: Any):
        try:
            return str(o)
        except Exception:
            return "<unserialisable>"

    return json.dumps(obj, default=default, indent=indent)
