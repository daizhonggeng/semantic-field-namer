from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.core.config import get_settings


@dataclass
class QdrantHit:
    score: float
    payload: dict[str, Any]


class QdrantService:
    def __init__(self, vector_size: int) -> None:
        self.settings = get_settings()
        self.vector_size = vector_size
        self._client = None

    def _get_client(self):  # noqa: ANN202
        if self._client is not None:
            return self._client
        try:
            from qdrant_client import QdrantClient

            self._client = QdrantClient(
                url=self.settings.qdrant_url,
                api_key=self.settings.qdrant_api_key,
                timeout=10,
                check_compatibility=False,
            )
            return self._client
        except Exception:
            return None

    def ensure_collection(self) -> None:
        client = self._get_client()
        if client is None:
            return
        try:
            from qdrant_client.http import models

            collections = {collection.name for collection in client.get_collections().collections}
            if self.settings.qdrant_collection not in collections:
                client.create_collection(
                    collection_name=self.settings.qdrant_collection,
                    vectors_config=models.VectorParams(size=self.vector_size, distance=models.Distance.COSINE),
                )
        except Exception:
            return

    def upsert_mapping(self, point_id: str, vector: list[float], payload: dict[str, Any]) -> None:
        client = self._get_client()
        if client is None:
            return
        self.ensure_collection()
        try:
            client.upsert(
                collection_name=self.settings.qdrant_collection,
                points=[{"id": point_id, "vector": vector, "payload": payload}],
            )
        except Exception:
            return

    def delete_mapping(self, point_id: str) -> None:
        client = self._get_client()
        if client is None:
            return
        try:
            from qdrant_client.http import models

            client.delete(
                collection_name=self.settings.qdrant_collection,
                points_selector=models.PointIdsList(points=[point_id]),
            )
        except Exception:
            return

    def search(self, project_id: int, vector: list[float], limit: int = 8) -> list[QdrantHit]:
        client = self._get_client()
        if client is None:
            return []
        try:
            from qdrant_client.http import models

            results = client.search(
                collection_name=self.settings.qdrant_collection,
                query_vector=vector,
                limit=limit,
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="project_id",
                            match=models.MatchValue(value=project_id),
                        )
                    ]
                ),
            )
            return [QdrantHit(score=float(item.score), payload=item.payload or {}) for item in results]
        except Exception:
            return []

    def health(self) -> dict[str, Any]:
        client = self._get_client()
        checked_at = datetime.now(UTC)
        if client is None:
            return {"configured": False, "reachable": False, "checked_at": checked_at, "error": "qdrant_client not available"}
        try:
            client.get_collections()
            return {"configured": True, "reachable": True, "checked_at": checked_at, "error": None}
        except Exception as exc:
            return {"configured": True, "reachable": False, "checked_at": checked_at, "error": str(exc)}
