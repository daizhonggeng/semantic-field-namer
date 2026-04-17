from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock
from typing import Any
from uuid import uuid4


@dataclass
class GenerationTaskState:
    task_id: str
    project_id: int
    status: str = "queued"
    stage: str = "queued"
    message: str = "任务已创建"
    progress: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    result: dict[str, Any] | None = None
    error: str | None = None


class GenerationTaskManager:
    def __init__(self) -> None:
        self._lock = Lock()
        self._tasks: dict[str, GenerationTaskState] = {}

    def create_task(self, project_id: int) -> GenerationTaskState:
        with self._lock:
            task = GenerationTaskState(task_id=str(uuid4()), project_id=project_id)
            self._tasks[task.task_id] = task
            return task

    def update_task(
        self,
        task_id: str,
        *,
        status: str | None = None,
        stage: str | None = None,
        message: str | None = None,
        progress: int | None = None,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> GenerationTaskState | None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            if status is not None:
                task.status = status
            if stage is not None:
                task.stage = stage
            if message is not None:
                task.message = message
            if progress is not None:
                task.progress = progress
            if result is not None:
                task.result = result
            if error is not None:
                task.error = error
            task.updated_at = datetime.now(UTC)
            return task

    def get_task(self, task_id: str) -> GenerationTaskState | None:
        with self._lock:
            return self._tasks.get(task_id)
