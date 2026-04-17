from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    owned_projects: Mapped[list["Project"]] = relationship(back_populates="owner")
    memberships: Mapped[list["ProjectMember"]] = relationship(back_populates="user")


class AIConfigSource(TimestampMixin, Base):
    __tablename__ = "ai_config_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    provider_type: Mapped[str] = mapped_column(String(32), default="openai_compatible")
    base_url: Mapped[str] = mapped_column(String(512))
    api_key: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(128), default="gpt-5.4")
    timeout_seconds: Mapped[float] = mapped_column(Float, default=30.0)
    max_retries: Mapped[int] = mapped_column(Integer, default=2)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    owner: Mapped["User"] = relationship(back_populates="owned_projects")
    members: Mapped[list["ProjectMember"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    imports: Mapped[list["SchemaImport"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    style_profile: Mapped["StyleProfile | None"] = relationship(
        back_populates="project",
        uselist=False,
        cascade="all, delete-orphan",
    )
    generation_runs: Mapped[list["GenerationRun"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )


class ProjectMember(TimestampMixin, Base):
    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_member"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String(16), default="viewer")

    project: Mapped["Project"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="memberships")


class SchemaImport(TimestampMixin, Base):
    __tablename__ = "schema_imports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    source_type: Mapped[str] = mapped_column(String(16))
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    project: Mapped["Project"] = relationship(back_populates="imports")
    fields: Mapped[list["SchemaField"]] = relationship(back_populates="schema_import", cascade="all, delete-orphan")


class SchemaField(TimestampMixin, Base):
    __tablename__ = "schema_fields"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    schema_import_id: Mapped[int | None] = mapped_column(ForeignKey("schema_imports.id"), nullable=True)
    table_name: Mapped[str] = mapped_column(String(128), index=True)
    column_name: Mapped[str] = mapped_column(String(128))
    column_comment_zh: Mapped[str | None] = mapped_column(String(255), nullable=True)
    canonical_comment_zh: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    data_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_type: Mapped[str] = mapped_column(String(16), default="import")

    schema_import: Mapped["SchemaImport | None"] = relationship(back_populates="fields")


class SemanticMapping(TimestampMixin, Base):
    __tablename__ = "semantic_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    canonical_zh: Mapped[str] = mapped_column(String(255), index=True)
    alias_zh_list: Mapped[list[str]] = mapped_column(JSON, default=list)
    english_name: Mapped[str] = mapped_column(String(128), index=True)
    table_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_type: Mapped[str] = mapped_column(String(16), default="import")
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class StyleProfile(TimestampMixin, Base):
    __tablename__ = "style_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), unique=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    stats: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    abbreviations: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    model_summary_source: Mapped[str] = mapped_column(String(32), default="heuristic")

    project: Mapped["Project"] = relationship(back_populates="style_profile")


class GenerationRun(TimestampMixin, Base):
    __tablename__ = "generation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    table_name: Mapped[str] = mapped_column(String(128))
    request_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    project: Mapped["Project"] = relationship(back_populates="generation_runs")
    items: Mapped[list["GenerationItem"]] = relationship(back_populates="generation_run", cascade="all, delete-orphan")


class GenerationItem(TimestampMixin, Base):
    __tablename__ = "generation_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    generation_run_id: Mapped[int] = mapped_column(ForeignKey("generation_runs.id"))
    comment_zh: Mapped[str] = mapped_column(String(255))
    proposed_name: Mapped[str] = mapped_column(String(128))
    source: Mapped[str] = mapped_column(String(32))
    similarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    matched_reference: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    conflict_flags: Mapped[list[str]] = mapped_column(JSON, default=list)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_new_term: Mapped[bool] = mapped_column(Boolean, default=False)

    generation_run: Mapped["GenerationRun"] = relationship(back_populates="items")
