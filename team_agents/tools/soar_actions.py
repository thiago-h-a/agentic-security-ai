"""
soar_actions.py – SOAR platform wrapper (sync).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel, Field, ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_env, get_httpx_client

logger = logging.getLogger(__name__)

class SOARAction(BaseModel):
    action_name: str = Field(..., description="Name of the action")
    parameters: Dict[str, Any] = Field(default_factory=dict)

class SOARResponse(BaseModel):
    status: str = Field(..., description="success | error")
    data: Optional[Dict[str, Any]] = Field(None)
    message: Optional[str] = Field(None)

_client = get_httpx_client()
_BASE_URL = get_env("SOAR_BASE_URL", "https://soar.example.com")
_TOKEN = get_env("SOAR_API_TOKEN")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8), reraise=True)
def perform_action(action: SOARAction) -> SOARResponse:
    url = f"{_BASE_URL.rstrip('/')}/api/actions/{action.action_name}"
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if _TOKEN:
        headers["Authorization"] = f"Bearer {_TOKEN}"

    try:
        resp = _client.post(url, json=action.dict(), headers=headers, timeout=10.0)
        resp.raise_for_status()
        parsed = SOARResponse.parse_obj(resp.json())
        logger.info("SOAR action '%s' executed", action.action_name)
        return parsed
    except (httpx.HTTPError, ValidationError) as exc:
        logger.error("SOAR action '%s' failed: %s", action.action_name, exc)
        return SOARResponse(status="error", message=str(exc))
