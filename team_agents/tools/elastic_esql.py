"""
elastic_esql.py – minimal ESQL runner wrapper (sync).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

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


# Load environment configuration
_ELASTIC_HOST: str = get_env("ELASTIC_HOST", "http://localhost:9200")
_ELASTIC_USER: Optional[str] = get_env("ELASTIC_USER")
_ELASTIC_PASSWORD: Optional[str] = get_env("ELASTIC_PASSWORD")
_ELASTIC_CA_CERTS: Optional[str] = get_env("ELASTIC_CA_CERTS")

es_client: Optional[Elasticsearch] = None
if Elasticsearch is not None:
    try:
        kwargs: Dict[str, Any] = {}

        # Add auth only if provided
        if _ELASTIC_USER and _ELASTIC_PASSWORD:
            kwargs["basic_auth"] = (_ELASTIC_USER, _ELASTIC_PASSWORD)

        # Add CA certs only if provided
        if _ELASTIC_CA_CERTS:
            kwargs["ca_certs"] = _ELASTIC_CA_CERTS
            kwargs["verify_certs"] = True
        else:
            # If host is https:// but no CA certs provided, disable verify
            kwargs["verify_certs"] = False

        es_client = Elasticsearch([_ELASTIC_HOST], **kwargs)

        # Sanity check connection (will raise if unreachable)
        info = es_client.info()
        logger.info("Connected to Elasticsearch cluster: %s", info.get("cluster_name"))

    except Exception as exc:
        logger.warning("Failed to construct Elasticsearch client: %s", exc)
        es_client = None


@retry(stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=1, min=1, max=8),
       reraise=True)
def run_query(payload: ESQLQuery) -> ESQLResponse:
    """
    Run an ESQL query against Elasticsearch and return structured response.
    """
    if not es_client:
        raise RuntimeError("Elasticsearch client is not configured or failed to connect")

    try:
        logger.info("Running ESQL query: %s", payload.query)
        raw = es_client.sql.query(body={"query": payload.query})
        parsed = ESQLResponse.parse_obj(raw)
        logger.info("ESQL query returned %d rows", len(parsed.rows))
        return parsed
    except (ValidationError, Exception) as exc:
        logger.exception("ESQL query failed: %s", exc)
        raise
