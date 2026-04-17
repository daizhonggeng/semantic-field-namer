from threading import Thread

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import ensure_editor_role, get_current_user, get_db, get_project_member
from app.core.database import SessionLocal
from app.models import SchemaField, StyleProfile, User
from app.schemas import (
    MatchingThresholds,
    StyleProfileResponse,
    StyleTaskCreateResponse,
    StyleTaskStatusResponse,
    StyleThresholdUpdateRequest,
)
from app.services.generation_task_manager import GenerationTaskManager
from app.services.llm_gateway import LlmGateway
from app.services.style_analyzer import analyze_style, resolve_matching_thresholds

router = APIRouter(prefix="/projects/{project_id}/style", tags=["style"])


@router.post("/analyze", response_model=StyleProfileResponse)
def analyze_project_style(
    project_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StyleProfileResponse:
    _, role = get_project_member(project_id, db, user)
    ensure_editor_role(role)
    fields = db.scalars(select(SchemaField).where(SchemaField.project_id == project_id)).all()
    llm_gateway = LlmGateway()
    stats, abbreviations, summary, source = analyze_style(fields, llm_gateway)
    profile = db.scalar(select(StyleProfile).where(StyleProfile.project_id == project_id))
    if profile is None:
        profile = StyleProfile(project_id=project_id)
        db.add(profile)
    existing_thresholds = resolve_matching_thresholds(profile.stats if profile else None)
    profile.stats = stats
    profile.stats["matching_thresholds"] = existing_thresholds
    profile.abbreviations = abbreviations
    profile.summary = summary
    profile.model_summary_source = source
    db.commit()
    db.refresh(profile)
    return StyleProfileResponse(
        project_id=project_id,
        summary=profile.summary,
        stats=profile.stats,
        abbreviations=profile.abbreviations,
        model_summary_source=profile.model_summary_source,
        matching_thresholds=MatchingThresholds(**resolve_matching_thresholds(profile.stats)),
        updated_at=profile.updated_at,
    )


@router.post("/analyze-task", response_model=StyleTaskCreateResponse)
def analyze_project_style_task(
    request: Request,
    project_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StyleTaskCreateResponse:
    _, role = get_project_member(project_id, db, user)
    ensure_editor_role(role)
    task_manager: GenerationTaskManager = request.app.state.style_tasks
    task = task_manager.create_task(project_id=project_id)
    thread = Thread(target=_run_style_analysis_task, args=(task.task_id, project_id, task_manager), daemon=True)
    thread.start()
    return StyleTaskCreateResponse(task_id=task.task_id)


@router.get("/analysis-tasks/{task_id}", response_model=StyleTaskStatusResponse)
def get_style_analysis_task(
    task_id: str,
    request: Request,
    project_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StyleTaskStatusResponse:
    get_project_member(project_id, db, user)
    task_manager: GenerationTaskManager = request.app.state.style_tasks
    task = task_manager.get_task(task_id)
    if task is None or task.project_id != project_id:
        raise HTTPException(status_code=404, detail="Style analysis task not found")
    result = StyleProfileResponse(**task.result) if task.result else None
    return StyleTaskStatusResponse(
        task_id=task.task_id,
        status=task.status,
        stage=task.stage,
        message=task.message,
        progress=task.progress,
        result=result,
        error=task.error,
    )


@router.get("/profile", response_model=StyleProfileResponse)
def get_style_profile(
    project_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StyleProfileResponse:
    get_project_member(project_id, db, user)
    profile = db.scalar(select(StyleProfile).where(StyleProfile.project_id == project_id))
    if profile is None:
        return StyleProfileResponse(
            project_id=project_id,
            summary="No style profile yet. Import schema and run analysis first.",
            stats={},
            abbreviations={},
            model_summary_source="none",
            matching_thresholds=MatchingThresholds(),
            updated_at=None,
        )
    return StyleProfileResponse(
        project_id=project_id,
        summary=profile.summary,
        stats=profile.stats,
        abbreviations=profile.abbreviations,
        model_summary_source=profile.model_summary_source,
        matching_thresholds=MatchingThresholds(**resolve_matching_thresholds(profile.stats)),
        updated_at=profile.updated_at,
    )


@router.put("/thresholds", response_model=StyleProfileResponse)
def update_style_thresholds(
    payload: StyleThresholdUpdateRequest,
    project_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StyleProfileResponse:
    _, role = get_project_member(project_id, db, user)
    ensure_editor_role(role)
    profile = db.scalar(select(StyleProfile).where(StyleProfile.project_id == project_id))
    if profile is None:
        profile = StyleProfile(project_id=project_id, stats={})
        db.add(profile)
    stats = dict(profile.stats or {})
    stats["matching_thresholds"] = payload.model_dump()
    profile.stats = stats
    if not profile.summary:
        profile.summary = "No style profile yet. Import schema and run analysis first."
    if not profile.model_summary_source:
        profile.model_summary_source = "none"
    db.commit()
    db.refresh(profile)
    return StyleProfileResponse(
        project_id=project_id,
        summary=profile.summary,
        stats=profile.stats,
        abbreviations=profile.abbreviations or {},
        model_summary_source=profile.model_summary_source,
        matching_thresholds=MatchingThresholds(**resolve_matching_thresholds(profile.stats)),
        updated_at=profile.updated_at,
    )


def _run_style_analysis_task(
    task_id: str,
    project_id: int,
    task_manager: GenerationTaskManager,
) -> None:
    db = SessionLocal()
    try:
        task_manager.update_task(task_id, status="running", stage="loading_fields", message="正在读取项目字段", progress=10)
        fields = db.scalars(select(SchemaField).where(SchemaField.project_id == project_id)).all()
        llm_gateway = LlmGateway()

        def progress_callback(stage: str, message: str, progress: int) -> None:
            task_manager.update_task(task_id, status="running", stage=stage, message=message, progress=progress)

        stats, abbreviations, summary, source = analyze_style(fields, llm_gateway, progress_callback=progress_callback)
        profile = db.scalar(select(StyleProfile).where(StyleProfile.project_id == project_id))
        if profile is None:
            profile = StyleProfile(project_id=project_id)
            db.add(profile)
        existing_thresholds = resolve_matching_thresholds(profile.stats if profile else None)
        profile.stats = stats
        profile.stats["matching_thresholds"] = existing_thresholds
        profile.abbreviations = abbreviations
        profile.summary = summary
        profile.model_summary_source = source
        db.commit()
        db.refresh(profile)
        task_manager.update_task(
            task_id,
            status="completed",
            stage="completed",
            message="风格分析完成",
            progress=100,
            result={
                "project_id": project_id,
                "summary": profile.summary,
                "stats": profile.stats,
                "abbreviations": profile.abbreviations,
                "model_summary_source": profile.model_summary_source,
                "matching_thresholds": resolve_matching_thresholds(profile.stats),
                "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
            },
        )
    except Exception as exc:
        task_manager.update_task(
            task_id,
            status="failed",
            stage="failed",
            message="风格分析失败",
            progress=100,
            error=str(exc),
        )
    finally:
        db.close()
