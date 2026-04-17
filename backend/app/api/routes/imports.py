from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import ensure_editor_role, get_current_user, get_db, get_project_member
from app.models import SchemaField, SchemaImport, SemanticMapping, User
from app.schemas import ImportedFieldResponse, ImportedFieldUpdateRequest, ImportResponse, JsonImportRequest, SqlImportRequest
from app.services.embedding_service import EmbeddingService
from app.services.import_service import parse_excel_fields, parse_json_fields, parse_sql_fields, parse_txt_fields
from app.services.normalization import normalize_comment
from app.services.qdrant_service import QdrantService

router = APIRouter(prefix="/projects/{project_id}/imports", tags=["imports"])


@router.post("/sql", response_model=ImportResponse)
def import_sql(
    payload: SqlImportRequest,
    project_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ImportResponse:
    _, role = get_project_member(project_id, db, user)
    ensure_editor_role(role)
    fields = parse_sql_fields(payload.sql)
    return _store_import(db, project_id, "sql", payload.source_name, {"sql": payload.sql}, fields)


@router.post("/json", response_model=ImportResponse)
def import_json(
    payload: JsonImportRequest,
    project_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ImportResponse:
    _, role = get_project_member(project_id, db, user)
    ensure_editor_role(role)
    fields = parse_json_fields(payload.fields)
    return _store_import(db, project_id, "json", payload.source_name, payload.model_dump(), fields)


@router.post("/excel", response_model=ImportResponse)
async def import_excel(
    project_id: int = Path(..., ge=1),
    source_name: str | None = Form(None),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ImportResponse:
    _, role = get_project_member(project_id, db, user)
    ensure_editor_role(role)
    file_bytes = await file.read()
    fields = parse_excel_fields(file_bytes)
    return _store_import(
        db,
        project_id,
        "excel",
        source_name or file.filename,
        {"filename": file.filename, "content_type": file.content_type},
        fields,
    )


@router.post("/txt", response_model=ImportResponse)
def import_txt(
    project_id: int = Path(..., ge=1),
    source_name: str | None = Form(None),
    content: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ImportResponse:
    _, role = get_project_member(project_id, db, user)
    ensure_editor_role(role)
    fields = parse_txt_fields(content)
    return _store_import(
        db,
        project_id,
        "txt",
        source_name or "txt-import",
        {"content_preview": content[:1000]},
        fields,
    )


@router.get("/fields", response_model=list[ImportedFieldResponse])
def list_imported_fields(
    project_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ImportedFieldResponse]:
    get_project_member(project_id, db, user)
    fields = db.scalars(
        select(SchemaField)
        .where(SchemaField.project_id == project_id)
        .order_by(SchemaField.table_name.asc(), SchemaField.id.asc())
    ).all()
    return [
        ImportedFieldResponse(
            id=field.id,
            table_name=field.table_name,
            column_name=field.column_name,
            column_comment_zh=field.column_comment_zh,
            canonical_comment_zh=field.canonical_comment_zh,
            data_type=field.data_type,
        )
        for field in fields
    ]


@router.put("/fields/{field_id}", response_model=ImportedFieldResponse)
def update_imported_field(
    payload: ImportedFieldUpdateRequest,
    project_id: int = Path(..., ge=1),
    field_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ImportedFieldResponse:
    _, role = get_project_member(project_id, db, user)
    ensure_editor_role(role)

    field = db.get(SchemaField, field_id)
    if field is None or field.project_id != project_id:
        raise HTTPException(status_code=404, detail="Imported field not found")

    old_table_name = field.table_name
    old_column_name = field.column_name

    field.table_name = payload.table_name.strip()
    field.column_name = payload.column_name.strip()
    field.column_comment_zh = payload.column_comment_zh.strip() if payload.column_comment_zh else None
    field.canonical_comment_zh = normalize_comment(field.column_comment_zh) if field.column_comment_zh else None
    field.data_type = payload.data_type.strip() if payload.data_type else None

    _sync_import_mapping(db, field, old_table_name, old_column_name)

    db.commit()
    db.refresh(field)
    return ImportedFieldResponse(
        id=field.id,
        table_name=field.table_name,
        column_name=field.column_name,
        column_comment_zh=field.column_comment_zh,
        canonical_comment_zh=field.canonical_comment_zh,
        data_type=field.data_type,
    )


def _store_import(
    db: Session,
    project_id: int,
    source_type: str,
    source_name: str | None,
    raw_payload: dict,
    fields: list[dict],
) -> ImportResponse:
    schema_import = SchemaImport(
        project_id=project_id,
        source_type=source_type,
        source_name=source_name,
        raw_payload=raw_payload,
    )
    db.add(schema_import)
    db.flush()

    embedding_service = EmbeddingService()
    qdrant_service = QdrantService(vector_size=embedding_service.dimension)
    vectors = embedding_service.embed([field["canonical_comment_zh"] or field["column_name"] for field in fields]) if fields else []
    mapped_count = 0
    comment_count = 0
    for field, vector in zip(fields, vectors, strict=True):
        schema_field = SchemaField(
            project_id=project_id,
            schema_import_id=schema_import.id,
            table_name=field["table_name"],
            column_name=field["column_name"],
            column_comment_zh=field["column_comment_zh"],
            canonical_comment_zh=field["canonical_comment_zh"],
            data_type=field["data_type"],
        )
        db.add(schema_field)
        if field["canonical_comment_zh"]:
            comment_count += 1
            mapping = SemanticMapping(
                project_id=project_id,
                canonical_zh=field["canonical_comment_zh"],
                alias_zh_list=[],
                english_name=field["column_name"],
                table_name=field["table_name"],
                source_type="import",
                confidence=1.0,
                confirmed=True,
            )
            db.add(mapping)
            db.flush()
            mapped_count += 1
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
    db.commit()
    return ImportResponse(
        import_id=schema_import.id,
        imported_count=len(fields),
        field_names=[field["column_name"] for field in fields],
        mapped_count=mapped_count,
        comment_count=comment_count,
    )


def _sync_import_mapping(db: Session, field: SchemaField, old_table_name: str, old_column_name: str) -> None:
    embedding_service = EmbeddingService()
    qdrant_service = QdrantService(vector_size=embedding_service.dimension)

    mapping = db.scalar(
        select(SemanticMapping).where(
            SemanticMapping.project_id == field.project_id,
            SemanticMapping.table_name == old_table_name,
            SemanticMapping.english_name == old_column_name,
            SemanticMapping.source_type == "import",
        )
    )

    if field.canonical_comment_zh:
        if mapping is None:
            mapping = SemanticMapping(
                project_id=field.project_id,
                canonical_zh=field.canonical_comment_zh,
                alias_zh_list=[],
                english_name=field.column_name,
                table_name=field.table_name,
                source_type="import",
                confidence=1.0,
                confirmed=True,
            )
            db.add(mapping)
            db.flush()
        else:
            mapping.canonical_zh = field.canonical_comment_zh
            mapping.english_name = field.column_name
            mapping.table_name = field.table_name
            mapping.confirmed = True
        vector = embedding_service.embed([field.canonical_comment_zh])[0]
        qdrant_service.upsert_mapping(
            point_id=f"{field.project_id}-{mapping.id}",
            vector=vector,
            payload={
                "project_id": field.project_id,
                "canonical_zh": mapping.canonical_zh,
                "alias_zh_list": mapping.alias_zh_list,
                "english_name": mapping.english_name,
                "table_name": mapping.table_name,
                "source_type": mapping.source_type,
                "confirmed": mapping.confirmed,
            },
        )
    elif mapping is not None:
        mapping_id = mapping.id
        db.delete(mapping)
        db.flush()
        qdrant_service.delete_mapping(point_id=f"{field.project_id}-{mapping_id}")
