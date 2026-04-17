from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models import AIConfigSource


@dataclass
class ActiveAIConfig:
    source_name: str
    provider_type: str
    base_url: str | None
    api_key: str | None
    model: str
    timeout_seconds: float
    max_retries: int
    from_storage: bool


def mask_api_key(api_key: str | None) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}"


def get_active_ai_config() -> ActiveAIConfig:
    settings = get_settings()
    db = SessionLocal()
    try:
        source = db.scalar(select(AIConfigSource).where(AIConfigSource.is_active.is_(True)).order_by(AIConfigSource.updated_at.desc()))
        if source is not None:
            return ActiveAIConfig(
                source_name=source.name,
                provider_type=source.provider_type,
                base_url=source.base_url,
                api_key=source.api_key,
                model=source.model,
                timeout_seconds=source.timeout_seconds,
                max_retries=source.max_retries,
                from_storage=True,
            )
    finally:
        db.close()

    return ActiveAIConfig(
        source_name="env-default",
        provider_type="openai_compatible",
        base_url=settings.openai_base_url,
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        timeout_seconds=settings.openai_timeout_seconds,
        max_retries=settings.openai_max_retries,
        from_storage=False,
    )
