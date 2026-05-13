from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings

# Load repo-root .env when running from apps/api
_root = Path(__file__).resolve().parents[3]
load_dotenv(_root / ".env")
load_dotenv(_root / "apps" / "api" / ".env")


class Settings(BaseSettings):
    database_url: str = "sqlite:///./kt_platform.db"
    cors_origins: str = "http://localhost:3000"
    jwt_secret: str = "dev-only-change-this-to-a-long-random-string-at-least-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    openai_api_key: str = ""
    openai_base_url: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    # Many corporate gateways expose chat/completions but not OpenAI-style embeddings.
    # When true, Chroma uses deterministic pseudo-embeddings while chat still uses the gateway.
    openai_use_pseudo_embeddings: bool = False

    chroma_persist_dir: str = "./chroma_data"
    data_upload_dir: str = "./uploads"
    expected_documents: int = 10

    model_config = {"env_file": ".env", "extra": "ignore"}

    @field_validator("jwt_secret", mode="before")
    @classmethod
    def _non_empty_jwt_secret(cls, v: object) -> object:
        # Empty JWT_SECRET in `.env` would otherwise override the dev default and break signing.
        if isinstance(v, str) and not v.strip():
            return "dev-only-change-this-to-a-long-random-string-at-least-32-chars"
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
