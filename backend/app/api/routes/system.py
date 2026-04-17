from fastapi import APIRouter, Depends, HTTPException, Path, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models import AIConfigSource, User
from app.schemas import AIConfigSourceCreateRequest, AIConfigSourceResponse, AIConfigSourceUpdateRequest, AiHealthResponse
from datetime import UTC, datetime

from app.services.ai_config_service import get_active_ai_config, mask_api_key
from app.services.llm_gateway import LlmGateway

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/ai-health", response_model=AiHealthResponse)
def ai_health(request: Request) -> AiHealthResponse:
    cached = getattr(request.app.state, "ai_health", None)
    if cached is None:
        cached = LlmGateway().health_check()
        request.app.state.ai_health = cached
    return AiHealthResponse(**cached)


@router.get("/ai-sources", response_model=list[AIConfigSourceResponse])
def list_ai_sources(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[AIConfigSourceResponse]:
    del user
    sources = db.scalars(select(AIConfigSource).order_by(AIConfigSource.created_at.asc())).all()
    responses = [
        AIConfigSourceResponse(
            id=source.id,
            name=source.name,
            provider_type=source.provider_type,
            base_url=source.base_url,
            model=source.model,
            timeout_seconds=source.timeout_seconds,
            max_retries=source.max_retries,
            is_active=source.is_active,
            is_readonly=False,
            api_key_masked=mask_api_key(source.api_key),
            created_at=source.created_at,
            updated_at=source.updated_at,
        )
        for source in sources
    ]
    active_config = get_active_ai_config()
    if not active_config.from_storage and active_config.base_url:
        now = datetime.now(UTC)
        responses.insert(
            0,
            AIConfigSourceResponse(
                id=0,
                name=active_config.source_name,
                provider_type=active_config.provider_type,
                base_url=active_config.base_url,
                model=active_config.model,
                timeout_seconds=active_config.timeout_seconds,
                max_retries=active_config.max_retries,
                is_active=True,
                is_readonly=True,
                api_key_masked=mask_api_key(active_config.api_key),
                created_at=now,
                updated_at=now,
            ),
        )
    return responses


@router.post("/ai-sources", response_model=AIConfigSourceResponse)
def create_ai_source(
    payload: AIConfigSourceCreateRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AIConfigSourceResponse:
    del user
    if payload.is_active:
        db.query(AIConfigSource).update({AIConfigSource.is_active: False})
    source = AIConfigSource(
        name=payload.name,
        provider_type=payload.provider_type,
        base_url=payload.base_url,
        api_key=payload.api_key,
        model=payload.model,
        timeout_seconds=payload.timeout_seconds,
        max_retries=payload.max_retries,
        is_active=payload.is_active,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    request.app.state.ai_health = None
    return AIConfigSourceResponse(
        id=source.id,
        name=source.name,
        provider_type=source.provider_type,
        base_url=source.base_url,
        model=source.model,
        timeout_seconds=source.timeout_seconds,
        max_retries=source.max_retries,
        is_active=source.is_active,
        is_readonly=False,
        api_key_masked=mask_api_key(source.api_key),
        created_at=source.created_at,
        updated_at=source.updated_at,
    )


@router.put("/ai-sources/{source_id}", response_model=AIConfigSourceResponse)
def update_ai_source(
    payload: AIConfigSourceUpdateRequest,
    request: Request,
    source_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AIConfigSourceResponse:
    del user
    source = db.get(AIConfigSource, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="AI source not found")
    if payload.is_active:
        db.query(AIConfigSource).update({AIConfigSource.is_active: False})
    source.name = payload.name
    source.provider_type = payload.provider_type
    source.base_url = payload.base_url
    if payload.api_key:
        source.api_key = payload.api_key
    source.model = payload.model
    source.timeout_seconds = payload.timeout_seconds
    source.max_retries = payload.max_retries
    source.is_active = payload.is_active
    db.commit()
    db.refresh(source)
    request.app.state.ai_health = None
    return AIConfigSourceResponse(
        id=source.id,
        name=source.name,
        provider_type=source.provider_type,
        base_url=source.base_url,
        model=source.model,
        timeout_seconds=source.timeout_seconds,
        max_retries=source.max_retries,
        is_active=source.is_active,
        is_readonly=False,
        api_key_masked=mask_api_key(source.api_key),
        created_at=source.created_at,
        updated_at=source.updated_at,
    )


@router.post("/ai-sources/{source_id}/activate", response_model=AIConfigSourceResponse)
def activate_ai_source(
    request: Request,
    source_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AIConfigSourceResponse:
    del user
    source = db.get(AIConfigSource, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="AI source not found")
    db.query(AIConfigSource).update({AIConfigSource.is_active: False})
    source.is_active = True
    db.commit()
    db.refresh(source)
    request.app.state.ai_health = None
    return AIConfigSourceResponse(
        id=source.id,
        name=source.name,
        provider_type=source.provider_type,
        base_url=source.base_url,
        model=source.model,
        timeout_seconds=source.timeout_seconds,
        max_retries=source.max_retries,
        is_active=source.is_active,
        is_readonly=False,
        api_key_masked=mask_api_key(source.api_key),
        created_at=source.created_at,
        updated_at=source.updated_at,
    )


@router.delete("/ai-sources/{source_id}")
def delete_ai_source(
    request: Request,
    source_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    del user
    source = db.get(AIConfigSource, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="AI source not found")
    db.delete(source)
    db.commit()
    request.app.state.ai_health = None
    return {"deleted": True, "source_id": source_id}
