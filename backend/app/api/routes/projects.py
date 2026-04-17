from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import ensure_editor_role, get_current_user, get_db, get_project_member
from app.models import GenerationRun, Project, ProjectMember, SchemaField, SemanticMapping, User
from app.schemas import (
    HistoryItemResponse,
    MappingConfirmRequest,
    ProjectCreate,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectUpdate,
    ShareRequest,
    UserOptionResponse,
)
from app.services.embedding_service import EmbeddingService
from app.services.normalization import normalize_comment
from app.services.qdrant_service import QdrantService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
def list_projects(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ProjectResponse]:
    projects = db.scalars(
        select(Project)
        .outerjoin(ProjectMember, Project.id == ProjectMember.project_id)
        .where(or_(Project.owner_id == user.id, ProjectMember.user_id == user.id))
        .order_by(Project.updated_at.desc())
    ).all()
    deduped = {project.id: project for project in projects}
    return [ProjectResponse.model_validate(project) for project in deduped.values()]


@router.post("", response_model=ProjectResponse)
def create_project(
    payload: ProjectCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    project = Project(name=payload.name, description=payload.description, owner_id=user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    payload: ProjectUpdate,
    project_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can update project")

    project.name = payload.name
    project.description = payload.description
    db.commit()
    db.refresh(project)
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}")
def delete_project(
    project_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can delete project")

    qdrant_service = QdrantService(vector_size=64)
    mappings = db.scalars(select(SemanticMapping).where(SemanticMapping.project_id == project_id)).all()
    for mapping in mappings:
        qdrant_service.delete_mapping(point_id=f"{project_id}-{mapping.id}")
        db.delete(mapping)

    fields = db.scalars(select(SchemaField).where(SchemaField.project_id == project_id)).all()
    for field in fields:
        db.delete(field)

    db.delete(project)
    db.commit()
    return {"deleted": True, "project_id": project_id}


@router.post("/{project_id}/share", response_model=ProjectMemberResponse)
def share_project(
    payload: ShareRequest,
    project_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectMemberResponse:
    _, role = get_project_member(project_id, db, user)
    if role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can manage members")
    target_user = db.scalar(select(User).where(User.username == payload.username))
    if target_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")
    membership = db.scalar(
        select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == target_user.id)
    )
    if membership is None:
        membership = ProjectMember(project_id=project_id, user_id=target_user.id, role=payload.role)
        db.add(membership)
    else:
        membership.role = payload.role
    db.commit()
    db.refresh(membership)
    return ProjectMemberResponse(
        id=membership.id,
        username=target_user.username,
        role=membership.role,
        created_at=membership.created_at,
    )


@router.get("/{project_id}/members", response_model=list[ProjectMemberResponse])
def list_members(
    project_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ProjectMemberResponse]:
    project, _ = get_project_member(project_id, db, user)
    members = db.scalars(select(ProjectMember).where(ProjectMember.project_id == project.id)).all()
    results = [
        ProjectMemberResponse(
            id=0,
            username=project.owner.username,
            role="owner",
            created_at=project.created_at,
        )
    ]
    for membership in members:
        results.append(
            ProjectMemberResponse(
                id=membership.id,
                username=membership.user.username,
                role=membership.role,
                created_at=membership.created_at,
            )
        )
    return results


@router.get("/{project_id}/share-candidates", response_model=list[UserOptionResponse])
def list_share_candidates(
    project_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[UserOptionResponse]:
    project, role = get_project_member(project_id, db, user)
    if role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can manage members")

    existing_user_ids = {project.owner_id}
    existing_user_ids.update(
        db.scalars(select(ProjectMember.user_id).where(ProjectMember.project_id == project_id)).all()
    )
    users = db.scalars(select(User).order_by(User.username.asc())).all()
    return [
        UserOptionResponse(id=target.id, username=target.username)
        for target in users
        if target.id not in existing_user_ids
    ]


@router.post("/{project_id}/mappings/confirm")
def confirm_mappings(
    payload: MappingConfirmRequest,
    project_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    _, role = get_project_member(project_id, db, user)
    ensure_editor_role(role)
    embedding_service = EmbeddingService()
    qdrant_service = QdrantService(vector_size=embedding_service.dimension)
    vectors = embedding_service.embed([item.canonical_zh for item in payload.items])
    inserted = 0
    for item, vector in zip(payload.items, vectors, strict=True):
        mapping = SemanticMapping(
            project_id=project_id,
            canonical_zh=normalize_comment(item.canonical_zh),
            alias_zh_list=[normalize_comment(alias) for alias in item.alias_zh_list],
            english_name=item.english_name,
            table_name=item.table_name,
            source_type="manual",
            confidence=1.0,
            confirmed=True,
            notes=item.notes,
        )
        db.add(mapping)
        db.flush()
        qdrant_service.upsert_mapping(
            point_id=f"{project_id}-{mapping.id}",
            vector=vector,
            payload={
                "project_id": project_id,
                "canonical_zh": mapping.canonical_zh,
                "alias_zh_list": mapping.alias_zh_list,
                "english_name": mapping.english_name,
                "table_name": mapping.table_name,
                "source_type": mapping.source_type,
                "confirmed": mapping.confirmed,
            },
        )
        inserted += 1
    db.commit()
    return {"inserted": inserted}
