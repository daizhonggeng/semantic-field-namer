from threading import Thread

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import ensure_editor_role, get_current_user, get_db, get_project_member
from app.core.database import SessionLocal
from app.models import GenerationRun, User
from app.schemas import GenerateRequest, GenerateResponse, GenerationTaskCreateResponse, GenerationTaskStatusResponse, HistoryItemResponse
from app.services.generation_task_manager import GenerationTaskManager
from app.services.embedding_service import EmbeddingService
from app.services.generation_service import FieldGenerationService
from app.services.llm_gateway import LlmGateway
from app.services.qdrant_service import QdrantService

router = APIRouter(prefix="/projects/{project_id}", tags=["generation"])


@router.post("/fields/generate", response_model=GenerateResponse)
def generate_fields(
    payload: GenerateRequest,
    project_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GenerateResponse:
    _, role = get_project_member(project_id, db, user)
    ensure_editor_role(role)
    embedding_service = EmbeddingService()
    qdrant_service = QdrantService(vector_size=embedding_service.dimension)
    llm_gateway = LlmGateway()
    service = FieldGenerationService(db, embedding_service, qdrant_service, llm_gateway)
    run, results, ai_used = service.generate(project_id, payload)
    return GenerateResponse(run_id=run.id, table_name=payload.table_name, ai_fallback_used=ai_used, results=results)


@router.post("/fields/generate-task", response_model=GenerationTaskCreateResponse)
def create_generation_task(
    payload: GenerateRequest,
    request: Request,
    project_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GenerationTaskCreateResponse:
    _, role = get_project_member(project_id, db, user)
    ensure_editor_role(role)
    task_manager: GenerationTaskManager = request.app.state.generation_tasks
    task = task_manager.create_task(project_id=project_id)
    thread = Thread(target=_run_generation_task, args=(task.task_id, project_id, payload, task_manager), daemon=True)
    thread.start()
    return GenerationTaskCreateResponse(task_id=task.task_id)


@router.get("/generation-tasks/{task_id}", response_model=GenerationTaskStatusResponse)
def get_generation_task(
    task_id: str,
    request: Request,
    project_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GenerationTaskStatusResponse:
    get_project_member(project_id, db, user)
    task_manager: GenerationTaskManager = request.app.state.generation_tasks
    task = task_manager.get_task(task_id)
    if task is None or task.project_id != project_id:
        raise HTTPException(status_code=404, detail="Generation task not found")
    result = GenerateResponse(**task.result) if task.result else None
    return GenerationTaskStatusResponse(
        task_id=task.task_id,
        status=task.status,
        stage=task.stage,
        message=task.message,
        progress=task.progress,
        result=result,
        error=task.error,
    )


@router.get("/generation-runs", response_model=list[HistoryItemResponse])
def generation_history(
    project_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[HistoryItemResponse]:
    get_project_member(project_id, db, user)
    runs = db.scalars(
        select(GenerationRun).where(GenerationRun.project_id == project_id).order_by(GenerationRun.created_at.desc())
    ).all()
    return [
        HistoryItemResponse(id=run.id, table_name=run.table_name, created_at=run.created_at, summary=run.summary)
        for run in runs
    ]


def _run_generation_task(
    task_id: str,
    project_id: int,
    payload: GenerateRequest,
    task_manager: GenerationTaskManager,
) -> None:
    db = SessionLocal()
    try:
        task_manager.update_task(task_id, status="running", stage="preparing", message="正在准备字段生成任务", progress=5)
        embedding_service = EmbeddingService()
        qdrant_service = QdrantService(vector_size=embedding_service.dimension)
        llm_gateway = LlmGateway()
        service = FieldGenerationService(db, embedding_service, qdrant_service, llm_gateway)

        def progress_callback(stage: str, message: str, progress: int) -> None:
            task_manager.update_task(task_id, status="running", stage=stage, message=message, progress=progress)

        run, results, ai_used = service.generate(project_id, payload, progress_callback=progress_callback)
        task_manager.update_task(
            task_id,
            status="completed",
            stage="completed",
            message="字段生成完成",
            progress=100,
            result={
                "run_id": run.id,
                "table_name": payload.table_name,
                "ai_fallback_used": ai_used,
                "results": [item.model_dump() for item in results],
            },
        )
    except Exception as exc:
        task_manager.update_task(
            task_id,
            status="failed",
            stage="failed",
            message="字段生成失败",
            progress=100,
            error=str(exc),
        )
    finally:
        db.close()
