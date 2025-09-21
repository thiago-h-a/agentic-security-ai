"""
core/llm.py — Async LLM wrapper and LangChain integrations.

Provides:
 - AsyncChatLLM: thin async wrapper around LangChain ChatOpenAI with fallback.
 - embedder() placeholder for vectorization (expandable).
 - safe_ask_llm(prompt, max_tokens=512) coroutine returns dict with 'text' and raw `llm_response`.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional
from team_agents.core.config import settings

OPENAI_API_KEY = settings.openai_api_key
OPENAI_LLM_DEFAULT_MODEL = settings.openai_llm_default_model
OPENAI_LLM_DEFAULT_TEMPERATURE = settings.openai_llm_default_temperature
OPENAI_LLM_DEFAULT_EMBEDDING_MODEL = settings.openai_llm_default_embedding_model


logger = logging.getLogger(__name__)

# LangChain modern imports
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from langchain_openai import OpenAIEmbeddings
LANGCHAIN_AVAILABLE = True

class AsyncChatLLM:
    """
    Async wrapper over LangChain ChatOpenAI (or a simulator).
    - If OPENAI_API_KEY is set and langchain is installed, uses real model.
    - Otherwise returns deterministic simulated responses for offline testing.
    """

    def __init__(self, model_name: str = OPENAI_LLM_DEFAULT_MODEL, temperature: float = OPENAI_LLM_DEFAULT_TEMPERATURE):
        self.model_name = model_name
        self.temperature = temperature
        self._client = None
        if LANGCHAIN_AVAILABLE and OPENAI_API_KEY:
            try:
                # ChatOpenAI supports async via .achat in recent LangChain; we will dynamically use it.
                self._client = ChatOpenAI(model_name=model_name, temperature=temperature, openai_api_key=OPENAI_API_KEY)
            except Exception as exc:
                logger.warning("Failed to instantiate ChatOpenAI: %s", exc)
                self._client = None

    async def ask(self, prompt: str, max_tokens: int = 512) -> Dict[str, Any]:
        """
        Ask the LLM asynchronously. Returns {'text': str, 'raw': object}
        TO DO: Implement logic of 'max_tokens'
        """
        if self._client is not None:
            try:
                # Prefer .achat if present (async), otherwise call in threadpool
                if hasattr(self._client, "achat"):
                    # construct a single human message
                    msg = HumanMessage(content=prompt)
                    resp = await self._client.achat([msg])  # type: ignore
                    text = getattr(resp, "content", None) or "".join(m.content for m in getattr(resp, "generations", []))
                    return {"text": text, "raw": resp}
                else:
                    # fallback: run sync in thread
                    loop = asyncio.get_event_loop()
                    resp = await loop.run_in_executor(None, self._client.generate, [HumanMessage(content=prompt)])  # type: ignore
                    # resp may be complex; attempt extraction
                    text = ""
                    try:
                        text = resp.generations[0][0].text  # type: ignore
                    except Exception:
                        text = str(resp)
                    return {"text": text, "raw": resp}
            except Exception as exc:
                logger.exception("LLM call failed: %s", exc)
                # continue to fallback simulator
        # Simulator fallback
        await asyncio.sleep(0.05)
        simulated = f"[SIMULATED:{self.model_name}] {prompt[:160]}{'...' if len(prompt) > 160 else ''}"
        return {"text": simulated, "raw": None}

# Instantiate a global LLM instance for use by team_agents (async-friendly)
llm = AsyncChatLLM()

# Placeholder: simple synchronous embedder stub (replace with real embeddings provider)
def embedder(text: str) -> list[float]:
    try:
        """
        Embed text using OpenAI embeddings via LangChain.
        You’ll need to have your OPENAI_API_KEY set as an environment variable
        """
        import os
        os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY
        embedding_model = OpenAIEmbeddings(model=OPENAI_LLM_DEFAULT_EMBEDDING_MODEL)
        return embedding_model.embed_query(text)
    except Exception as e:
        # deterministic trivial embedding for demo purposes
        logger.exception("Embedding call failed: %s", e)
        return [float(ord(c) % 97) / 97.0 for c in text[:128]]

async def safe_ask_llm(prompt: str, max_tokens: int = 512) -> Dict[str, Any]:
    return await llm.ask(prompt, max_tokens=max_tokens)
