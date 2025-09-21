"""
cti_feed.py – CTI feed ingestion helpers (sync).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

import httpx
from pydantic import BaseModel, Field, ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_env, get_httpx_client

logger = logging.getLogger(__name__)

class CTIItem(BaseModel):
    id: str = Field(..., description="Unique identifier")
    type: str = Field(..., description="Item type")
    attributes: Dict[str, Any] = Field(default_factory=dict)

_client = get_httpx_client()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8), reraise=True)
def _fetch(url: str, headers: Dict[str, str]) -> httpx.Response:
    return _client.get(url, headers=headers, timeout=10.0)

def fetch_feed(url: str | None = None) -> List[CTIItem]:
    url = url or get_env("CTI_FEED_URL", "https://cti.example.com/feed")
    headers: Dict[str, str] = {}
    token = get_env("CTI_FEED_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    logger.info("Fetching CTI feed from %s", url)
    try:
        resp = _fetch(url, headers)
        data = resp.json()
        items = [CTIItem.parse_obj(item) for item in data.get("data", [])]
        logger.info("Parsed %d CTI items", len(items))
        return items
    except (httpx.HTTPError, ValidationError, ValueError) as exc:
        logger.error("Failed to fetch or parse CTI feed: %s", exc)
        return []
