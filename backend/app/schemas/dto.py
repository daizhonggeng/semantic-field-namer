from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class UserLogin(UserCreate):
    pass


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    owner_id: int
    created_at: datetime
    updated_at: datetime


class ProjectMemberResponse(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime


class UserOptionResponse(BaseModel):
    id: int
    username: str


class ShareRequest(BaseModel):
    username: str
    role: str = Field(pattern="^(owner|editor|viewer)$")


class SqlImportRequest(BaseModel):
    source_name: str | None = None
    sql: str


class JsonFieldInput(BaseModel):
    table_name: str
    column_name: str
    column_comment_zh: str | None = None
    data_type: str | None = None


class JsonImportRequest(BaseModel):
    source_name: str | None = None
    fields: list[JsonFieldInput] = Field(default_factory=list)


class ImportResponse(BaseModel):
    import_id: int
    imported_count: int
    field_names: list[str]
    mapped_count: int = 0
    comment_count: int = 0


class ImportedFieldResponse(BaseModel):
    id: int
    table_name: str
    column_name: str
    column_comment_zh: str | None = None
    canonical_comment_zh: str | None = None
    data_type: str | None = None


class ImportedFieldUpdateRequest(BaseModel):
    table_name: str = Field(min_length=1, max_length=128)
    column_name: str = Field(min_length=1, max_length=128)
    column_comment_zh: str | None = Field(default=None, max_length=255)
    data_type: str | None = Field(default=None, max_length=64)


class MatchingThresholds(BaseModel):
    lexical_threshold: float = Field(default=0.9, ge=0.0, le=1.0)
    semantic_score_threshold: float = Field(default=0.82, ge=0.0, le=1.0)
    semantic_gap_threshold: float = Field(default=0.06, ge=0.0, le=1.0)


class StyleProfileResponse(BaseModel):
    project_id: int
    summary: str
    stats: dict[str, Any]
    abbreviations: dict[str, str]
    model_summary_source: str
    matching_thresholds: MatchingThresholds
    updated_at: datetime | None = None


class StyleThresholdUpdateRequest(MatchingThresholds):
    pass


class StyleTaskCreateResponse(BaseModel):
    task_id: str


class StyleTaskStatusResponse(BaseModel):
    task_id: str
    status: str
    stage: str
    message: str
    progress: int
    result: StyleProfileResponse | None = None
    error: str | None = None


class GenerateFieldInput(BaseModel):
    comment_zh: str
    data_type: str | None = None
    nullable: bool = True
    extra_context: str | None = None


class GenerateRequest(BaseModel):
    table_name: str
    db_type: str = "pg"
    existing_columns: list[str] = Field(default_factory=list)
    items: list[GenerateFieldInput]
    preview_only: bool = True


class GeneratedFieldResult(BaseModel):
    comment_zh: str
    proposed_name: str
    source: str
    similarity_score: float | None = None
    matched_reference: dict[str, Any] | None = None
    conflict_flags: list[str] = Field(default_factory=list)
    reason: str | None = None
    is_new_term: bool = False


class GenerateResponse(BaseModel):
    run_id: int
    table_name: str
    ai_fallback_used: bool
    results: list[GeneratedFieldResult]


class GenerationTaskCreateResponse(BaseModel):
    task_id: str


class GenerationTaskStatusResponse(BaseModel):
    task_id: str
    status: str
    stage: str
    message: str
    progress: int
    result: GenerateResponse | None = None
    error: str | None = None


class MappingConfirmItem(BaseModel):
    canonical_zh: str
    english_name: str
    alias_zh_list: list[str] = Field(default_factory=list)
    table_name: str | None = None
    notes: str | None = None


class MappingConfirmRequest(BaseModel):
    items: list[MappingConfirmItem]


class HistoryItemResponse(BaseModel):
    id: int
    table_name: str
    created_at: datetime
    summary: dict[str, Any]


class AiHealthResponse(BaseModel):
    configured: bool
    reachable: bool
    model_checked: bool
    fallback_needed: bool
    base_url: str | None
    source_name: str | None = None
    provider_type: str | None = None
    model: str
    checked_at: datetime | None
    error: str | None = None


class AIConfigSourceCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    provider_type: str = Field(default="openai_compatible", pattern="^openai_compatible$")
    base_url: str = Field(min_length=1, max_length=512)
    api_key: str = Field(min_length=1)
    model: str = Field(default="gpt-5.4", min_length=1, max_length=128)
    timeout_seconds: float = Field(default=30.0, ge=1, le=300)
    max_retries: int = Field(default=2, ge=0, le=10)
    is_active: bool = False


class AIConfigSourceUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    provider_type: str = Field(default="openai_compatible", pattern="^openai_compatible$")
    base_url: str = Field(min_length=1, max_length=512)
    api_key: str | None = None
    model: str = Field(default="gpt-5.4", min_length=1, max_length=128)
    timeout_seconds: float = Field(default=30.0, ge=1, le=300)
    max_retries: int = Field(default=2, ge=0, le=10)
    is_active: bool = False


class AIConfigSourceResponse(BaseModel):
    id: int
    name: str
    provider_type: str
    base_url: str
    model: str
    timeout_seconds: float
    max_retries: int
    is_active: bool
    is_readonly: bool = False
    api_key_masked: str
    created_at: datetime
    updated_at: datetime
