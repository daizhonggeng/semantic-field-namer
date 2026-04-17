from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, generation, imports, projects, style, system
from app.core.config import get_settings
from app.core.database import Base, engine
from app.services.embedding_service import EmbeddingService
from app.services.llm_gateway import LlmGateway
from app.services.generation_task_manager import GenerationTaskManager
from app.services.qdrant_service import QdrantService


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    embedding_service = EmbeddingService()
    qdrant_service = QdrantService(vector_size=embedding_service.dimension)
    qdrant_service.ensure_collection()
    app.state.ai_health = LlmGateway().health_check()
    app.state.qdrant_health = qdrant_service.health()
    app.state.generation_tasks = GenerationTaskManager()
    app.state.style_tasks = GenerationTaskManager()
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(projects.router, prefix=settings.api_prefix)
app.include_router(imports.router, prefix=settings.api_prefix)
app.include_router(style.router, prefix=settings.api_prefix)
app.include_router(generation.router, prefix=settings.api_prefix)
app.include_router(system.router, prefix=settings.api_prefix)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Semantic Field Namer API"}
