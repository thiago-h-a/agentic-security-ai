"""
config.py – central configuration loader.

Provides:
 - get_env(name, default)
 - synchronous HTTPX client providers
 - retry decorator factory
"""
from __future__ import annotations

import os
import logging
from functools import lru_cache
from typing import Optional

import httpx
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

logger = logging.getLogger(__name__)

def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name, default)
    if value is None:
        logger.debug("Environment variable %s not set; using default %s", name, default)
    return value

DEFAULT_TIMEOUT = httpx.Timeout(10.0, connect=5.0)

@lru_cache(maxsize=1)
def get_httpx_client() -> httpx.Client:
    return httpx.Client(timeout=DEFAULT_TIMEOUT, follow_redirects=True)

@lru_cache(maxsize=1)
def get_async_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True)

def retry_decorator():
    return retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )

__all__ = ["get_env", "get_httpx_client", "get_async_client", "retry_decorator"]
