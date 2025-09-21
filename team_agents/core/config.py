import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_llm_default_model: str = os.getenv("OPENAI_LLM_DEFAULT_MODEL", "gpt-4o-mini")
    openai_llm_default_temperature: float = os.getenv("OPENAI_LLM_DEFAULT_TEMPERATURE", 0.0)
    openai_llm_default_embedding_model: str = os.getenv("OPENAI_LLM_DEFAULT_EMBEDDING_MODEL", "text-embedding-3-small")
    env: str = os.getenv("ENV", "dev")

settings = Settings()
