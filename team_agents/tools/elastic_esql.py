"""
elastic_esql.py – minimal ESQL runner wrapper (sync).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from pydantic import BaseModel, Field, ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from fastAPI.config import get_env

logger = logging.getLogger(__name__)

try:
    from elasticsearch import Elasticsearch  # type: ignore
except Exception:
    Elasticsearch = None  # type: ignore

class ESQLQuery(BaseModel):
    query: str = Field(...)

class ESQLResponse(BaseModel):
    columns: List[Dict[str, Any]] = Field(...)
    rows: List[List[Any]] = Field(...)

_ELASTIC_HOST = get_env("ELASTIC_HOST", "http://localhost:9200")
_ELASTIC_USER = get_env("ELASTIC_USER")
_ELASTIC_PASSWORD = get_env("ELASTIC_PASSWORD")
_ELASTIC_CA_CERTS = get_env("ELASTIC_CA_CERTS")

es_client = None
if Elasticsearch is not None:
    try:
        es_client = Elasticsearch(
            [_ELASTIC_HOST],
            basic_auth=(_ELASTIC_USER, _ELASTIC_PASSWORD) if _ELASTIC_USER else None,
            ca_certs=_ELASTIC_CA_CERTS,
            request_timeout=30,
        )
    except Exception as exc:
        logger.warning("Failed to construct Elasticsearch client: %s", exc)
        es_client = None

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8), reraise=True)
def run_query(payload: ESQLQuery) -> ESQLResponse:
    if not es_client:
        raise RuntimeError("Elasticsearch client is not configured")

    try:
        logger.info("Running ESQL query: %s", payload.query)
        raw = es_client.sql.query(body={"query": payload.query})
        parsed = ESQLResponse.parse_obj(raw)
        logger.info("ESQL query returned %d rows", len(parsed.rows))
        return parsed
    except (ValidationError, Exception) as exc:
        logger.exception("ESQL query failed: %s", exc)
        raise
