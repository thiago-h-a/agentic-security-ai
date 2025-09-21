"""
schemas.py – Pydantic schemas for SecOps Graph tools.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

class Indicator(BaseModel):
    type: str = Field(..., description="Type of the indicator, e.g., 'ip', 'url'.")
    value: str = Field(..., description="The indicator value.")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)

class FeedResponse(BaseModel):
    indicators: List[Indicator] = Field(default_factory=list)

def parse_feed_response(data: Any) -> FeedResponse:
    try:
        return FeedResponse.parse_obj(data)
    except ValidationError as exc:
        logger.error("Failed to parse feed response: %s", exc)
        raise
