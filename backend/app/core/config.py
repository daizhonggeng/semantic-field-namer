from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Semantic Field Namer"
    api_prefix: str = "/api"
    secret_key: str = "change-this-in-production-with-at-least-32-bytes"
    access_token_expire_minutes: int = 60 * 24
    database_url: str = "sqlite:///./semantic_field_namer.db"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://127.0.0.1:5173", "http://localhost:5173"]
    )
    qdrant_url: str = "http://127.0.0.1:6333"
    qdrant_collection: str = "semantic_fields"
    qdrant_api_key: str | None = None
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-5.4"
    openai_timeout_seconds: float = 30.0
    openai_max_retries: int = 2
    sentence_transformer_model: str = "BAAI/bge-small-zh-v1.5"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
