from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.reserved_words import RESERVED_WORDS
from app.models import GenerationItem, GenerationRun, SchemaField, SemanticMapping, StyleProfile
from app.schemas.dto import GenerateRequest, GeneratedFieldResult
from app.services.embedding_service import EmbeddingService
from app.services.llm_gateway import LlmGateway
from app.services.normalization import normalize_comment, similarity, simple_translate, snake_case
from app.services.qdrant_service import QdrantService
from app.services.style_analyzer import resolve_matching_thresholds


@dataclass
class MatchCandidate:
    english_name: str
    source: str
    similarity_score: float | None = None
    matched_reference: dict[str, Any] | None = None
    reason: str | None = None
    is_new_term: bool = False


class FieldGenerationService:
    def __init__(
        self,
        db: Session,
        embedding_service: EmbeddingService,
        qdrant_service: QdrantService,
        llm_gateway: LlmGateway,
    ) -> None:
        self.db = db
        self.embedding_service = embedding_service
        self.qdrant_service = qdrant_service
        self.llm_gateway = llm_gateway

    def generate(
        self,
        project_id: int,
        request: GenerateRequest,
        progress_callback: Callable[[str, str, int], None] | None = None,
    ) -> tuple[GenerationRun, list[GeneratedFieldResult], bool]:
        self._report_progress(progress_callback, "preparing", "正在准备字段生成任务", 5)
        mappings = self.db.scalars(
            select(SemanticMapping).where(SemanticMapping.project_id == project_id).order_by(SemanticMapping.created_at.desc())
        ).all()
        style_profile = self.db.scalar(select(StyleProfile).where(StyleProfile.project_id == project_id))
        thresholds = resolve_matching_thresholds(style_profile.stats if style_profile else None)
        mapping_pool = self._build_mapping_pool(mappings)
        existing_names = set(request.existing_columns)
        existing_names.update(
            self.db.scalars(
                select(SchemaField.column_name).where(
                    SchemaField.project_id == project_id,
                    SchemaField.table_name == request.table_name,
                )
            ).all()
        )

        provisional_results: list[tuple[str, MatchCandidate]] = []

        self._report_progress(progress_callback, "exact_matching", "正在匹配本地映射池", 20)
        unresolved = []
        for item in request.items:
            normalized = normalize_comment(item.comment_zh)
            candidate = self._exact_match(normalized, mapping_pool)
            if candidate is None:
                unresolved.append(item)
                continue
            provisional_results.append((item.comment_zh, candidate))

        self._report_progress(progress_callback, "lexical_matching", "正在进行近似匹配", 40)
        lexical_unresolved = []
        for item in unresolved:
            candidate = self._lexical_match(item.comment_zh, mapping_pool, thresholds["lexical_threshold"])
            if candidate is None:
                lexical_unresolved.append(item)
                continue
            provisional_results.append((item.comment_zh, candidate))

        self._report_progress(progress_callback, "semantic_search", "正在匹配向量数据库", 60)
        semantic_unresolved = []
        for item in lexical_unresolved:
            candidate = self._semantic_match(
                project_id,
                item.comment_zh,
                thresholds["semantic_score_threshold"],
                thresholds["semantic_gap_threshold"],
            )
            if candidate is None:
                semantic_unresolved.append(item)
                continue
            provisional_results.append((item.comment_zh, candidate))

        ai_payload = None
        ai_used = False
        if semantic_unresolved:
            self._report_progress(progress_callback, "llm_generating", "正在调用大模型补全未命中字段", 80)
            ai_payload = {
                "style_summary": style_profile.summary if style_profile else "Use stable snake_case naming.",
                "style_stats": style_profile.stats if style_profile else {},
                "abbreviations": style_profile.abbreviations if style_profile else {},
                "table_name": request.table_name,
                "db_type": request.db_type,
                "items": [
                    {
                        "comment_zh": item.comment_zh,
                        "data_type": item.data_type,
                        "nullable": item.nullable,
                        "extra_context": item.extra_context,
                        "references": self._top_reference_candidates(project_id, item.comment_zh, mappings),
                    }
                    for item in semantic_unresolved
                ],
            }
            generated_items, ai_used = self.llm_gateway.generate_field_names(ai_payload)
            for generated in generated_items:
                provisional_results.append(
                    (
                        generated["comment_zh"],
                        MatchCandidate(
                            english_name=generated["candidate_name"],
                            source="llm" if ai_used else "heuristic",
                            similarity_score=float(generated.get("confidence", 0.0)),
                            matched_reference={"based_on": generated.get("based_on")},
                            reason=generated.get("rationale"),
                            is_new_term=bool(generated.get("is_new_term", True)),
                        ),
                    )
                )

        result_by_comment: dict[str, MatchCandidate] = defaultdict(
            lambda: MatchCandidate(english_name="", source="missing")
        )
        for comment, candidate in provisional_results:
            result_by_comment[comment] = candidate

        self._report_progress(progress_callback, "post_processing", "正在整理结果并检查冲突", 92)
        resolved_results: list[GeneratedFieldResult] = []
        used_names = set(existing_names)
        for item in request.items:
            candidate = result_by_comment[item.comment_zh]
            proposed_name, conflict_flags = self._ensure_valid_name(
                raw_name=candidate.english_name or simple_translate(item.comment_zh),
                comment_zh=item.comment_zh,
                used_names=used_names,
            )
            used_names.add(proposed_name)
            resolved_results.append(
                GeneratedFieldResult(
                    comment_zh=item.comment_zh,
                    proposed_name=proposed_name,
                    source=candidate.source,
                    similarity_score=candidate.similarity_score,
                    matched_reference=candidate.matched_reference,
                    conflict_flags=conflict_flags,
                    reason=candidate.reason,
                    is_new_term=candidate.is_new_term,
                )
            )

        generated_sql = self._build_create_table_sql(request.table_name, resolved_results)
        run = GenerationRun(
            project_id=project_id,
            table_name=request.table_name,
            request_payload=request.model_dump(),
            summary={
                "total": len(request.items),
                "ai_used": ai_used,
                "style_summary_present": bool(style_profile),
                "source_breakdown": self._source_breakdown(resolved_results),
                "matching_thresholds": thresholds,
                "generated_sql": generated_sql,
                "ai_payload": ai_payload if request.preview_only else None,
            },
        )
        self.db.add(run)
        self.db.flush()
        for result in resolved_results:
            self.db.add(
                GenerationItem(
                    generation_run_id=run.id,
                    comment_zh=result.comment_zh,
                    proposed_name=result.proposed_name,
                    source=result.source,
                    similarity_score=result.similarity_score,
                    matched_reference=result.matched_reference,
                    conflict_flags=result.conflict_flags,
                    reason=result.reason,
                    is_new_term=result.is_new_term,
                )
            )
        self.db.commit()
        self.db.refresh(run)
        self._report_progress(progress_callback, "completed", "字段生成完成", 100)
        return run, resolved_results, ai_used

    def _guess_column_type(self, item: GeneratedFieldResult) -> str:
        comment = item.comment_zh
        name = item.proposed_name
        if name == "id" or name.endswith("_id"):
            return "bigint"
        if name.startswith("is_") or name.endswith("_flag") or name.startswith("f_"):
            return "boolean"
        if name.endswith("_at") or name.endswith("_time"):
            return "timestamp"
        if name.endswith("_date"):
            return "date"
        if (
            "数量" in comment
            or "次数" in comment
            or "排序" in comment
            or name.endswith("_count")
            or name.endswith("_qty")
            or name.endswith("_sort")
        ):
            return "integer"
        return "varchar(255)"

    def _build_create_table_sql(self, table_name: str, results: list[GeneratedFieldResult]) -> str:
        column_lines = []
        comment_lines = []
        for item in results:
            column_type = self._guess_column_type(item)
            column_lines.append(f"  {item.proposed_name} {column_type}")
            escaped_comment = item.comment_zh.replace("'", "''")
            comment_lines.append(f"COMMENT ON COLUMN {table_name}.{item.proposed_name} IS '{escaped_comment}';")

        return "\n".join(
            [
                f"CREATE TABLE {table_name} (",
                *[f"{line}{',' if index < len(column_lines) - 1 else ''}" for index, line in enumerate(column_lines)],
                ");",
                "",
                f"COMMENT ON TABLE {table_name} IS '自动生成表';",
                *comment_lines,
            ]
        )

    def _source_breakdown(self, results: list[GeneratedFieldResult]) -> dict[str, int]:
        breakdown: dict[str, int] = {}
        for item in results:
            breakdown[item.source] = breakdown.get(item.source, 0) + 1
        return breakdown

    def _build_mapping_pool(self, mappings: list[SemanticMapping]) -> dict[str, SemanticMapping]:
        pool: dict[str, SemanticMapping] = {}
        for mapping in mappings:
            pool[mapping.canonical_zh] = mapping
            for alias in mapping.alias_zh_list:
                pool[normalize_comment(alias)] = mapping
        return pool

    def _exact_match(
        self,
        normalized: str,
        mapping_pool: dict[str, SemanticMapping],
    ) -> MatchCandidate | None:
        if normalized in mapping_pool:
            mapping = mapping_pool[normalized]
            return MatchCandidate(
                english_name=mapping.english_name,
                source="exact",
                similarity_score=1.0,
                matched_reference={"canonical_zh": mapping.canonical_zh, "english_name": mapping.english_name},
                reason="Matched canonical mapping",
            )
        return None

    def _lexical_match(
        self,
        raw_comment: str,
        mapping_pool: dict[str, SemanticMapping],
        lexical_threshold: float,
    ) -> MatchCandidate | None:
        lexical_best = None
        lexical_score = 0.0
        for key, mapping in mapping_pool.items():
            score = similarity(raw_comment, key)
            if score > lexical_score:
                lexical_score = score
                lexical_best = mapping
        if lexical_best and lexical_score >= lexical_threshold:
            return MatchCandidate(
                english_name=lexical_best.english_name,
                source="lexical",
                similarity_score=round(lexical_score, 4),
                matched_reference={"canonical_zh": lexical_best.canonical_zh, "english_name": lexical_best.english_name},
                reason="Matched lexical similarity",
            )
        return None

    def _semantic_match(
        self,
        project_id: int,
        raw_comment: str,
        semantic_score_threshold: float,
        semantic_gap_threshold: float,
    ) -> MatchCandidate | None:
        vector = self.embedding_service.embed([raw_comment])[0]
        hits = self.qdrant_service.search(project_id=project_id, vector=vector, limit=2)
        if hits:
            top_score = hits[0].score
            next_score = hits[1].score if len(hits) > 1 else 0.0
            if top_score >= semantic_score_threshold and (top_score - next_score) >= semantic_gap_threshold:
                return MatchCandidate(
                    english_name=hits[0].payload.get("english_name", simple_translate(raw_comment)),
                    source="semantic",
                    similarity_score=round(top_score, 4),
                    matched_reference=hits[0].payload,
                    reason="Matched semantic vector search",
                )
        return None

    def _report_progress(
        self,
        progress_callback: Callable[[str, str, int], None] | None,
        stage: str,
        message: str,
        progress: int,
    ) -> None:
        if progress_callback is not None:
            progress_callback(stage, message, progress)

    def _top_reference_candidates(
        self,
        project_id: int,
        comment_zh: str,
        mappings: list[SemanticMapping],
    ) -> list[dict[str, Any]]:
        vector = self.embedding_service.embed([comment_zh])[0]
        semantic_hits = self.qdrant_service.search(project_id=project_id, vector=vector, limit=3)
        if semantic_hits:
            return [hit.payload for hit in semantic_hits]
        lexical_candidates = sorted(
            mappings,
            key=lambda mapping: similarity(comment_zh, mapping.canonical_zh),
            reverse=True,
        )[:3]
        return [
            {
                "canonical_zh": mapping.canonical_zh,
                "english_name": mapping.english_name,
                "alias_zh_list": mapping.alias_zh_list,
            }
            for mapping in lexical_candidates
        ]

    def _ensure_valid_name(self, raw_name: str, comment_zh: str, used_names: set[str]) -> tuple[str, list[str]]:
        flags: list[str] = []
        proposed_name = snake_case(raw_name)
        if not proposed_name:
            proposed_name = simple_translate(comment_zh)
            flags.append("empty_fallback")
        if not re.match(r"^[a-z][a-z0-9_]*$", proposed_name):
            proposed_name = f"field_{proposed_name}".strip("_")
            flags.append("normalized_snake_case")
        if proposed_name in RESERVED_WORDS:
            proposed_name = f"{proposed_name}_field"
            flags.append("reserved_word")
        if proposed_name in used_names:
            suffix_parts = ["id", "code", "name", "flag", "type"]
            for suffix in suffix_parts:
                adjusted = proposed_name if proposed_name.endswith(f"_{suffix}") else f"{proposed_name}_{suffix}"
                if adjusted not in used_names and adjusted not in RESERVED_WORDS:
                    proposed_name = adjusted
                    flags.append("duplicate_resolved")
                    break
            counter = 2
            while proposed_name in used_names or proposed_name in RESERVED_WORDS:
                proposed_name = f"{snake_case(raw_name)}_{counter}"
                counter += 1
            if "duplicate_resolved" not in flags:
                flags.append("duplicate_resolved")
        return proposed_name, flags
