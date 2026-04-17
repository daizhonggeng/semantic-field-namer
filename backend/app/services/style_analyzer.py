from __future__ import annotations

from collections import Counter
from typing import Callable

from app.models import SchemaField
from app.services.llm_gateway import LlmGateway
from app.services.normalization import normalize_comment

COMMON_ABBREVIATIONS = {
    "number": "no",
    "amount": "amt",
    "quantity": "qty",
    "count": "cnt",
    "description": "desc",
    "address": "addr",
}

DEFAULT_MATCHING_THRESHOLDS = {
    "lexical_threshold": 0.9,
    "semantic_score_threshold": 0.82,
    "semantic_gap_threshold": 0.06,
}


def resolve_matching_thresholds(stats: dict | None) -> dict[str, float]:
    if not isinstance(stats, dict):
        return DEFAULT_MATCHING_THRESHOLDS.copy()
    configured = stats.get("matching_thresholds")
    if not isinstance(configured, dict):
        return DEFAULT_MATCHING_THRESHOLDS.copy()
    return {
        "lexical_threshold": float(configured.get("lexical_threshold", DEFAULT_MATCHING_THRESHOLDS["lexical_threshold"])),
        "semantic_score_threshold": float(
            configured.get("semantic_score_threshold", DEFAULT_MATCHING_THRESHOLDS["semantic_score_threshold"])
        ),
        "semantic_gap_threshold": float(
            configured.get("semantic_gap_threshold", DEFAULT_MATCHING_THRESHOLDS["semantic_gap_threshold"])
        ),
    }


def analyze_style(
    fields: list[SchemaField],
    llm_gateway: LlmGateway,
    progress_callback: Callable[[str, str, int], None] | None = None,
) -> tuple[dict, dict, str, str]:
    if progress_callback is not None:
        progress_callback("loading_fields", "正在读取项目字段", 15)
    english_names = [field.column_name for field in fields if field.column_name]
    if progress_callback is not None:
        progress_callback("calculating_stats", "正在统计命名风格", 45)
    snake_case_ratio = (
        sum(1 for name in english_names if name == name.lower() and "_" in name) / max(len(english_names), 1)
    )
    boolean_prefix_counter = Counter(
        name.split("_", 1)[0]
        for name in english_names
        if name.startswith(("is_", "has_", "can_", "f_", "flag_"))
    )
    id_suffix_counter = Counter(
        suffix
        for name in english_names
        for suffix in ("_id", "_no", "_code")
        if name.endswith(suffix)
    )
    datetime_suffix_counter = Counter(
        suffix
        for name in english_names
        for suffix in ("_at", "_time", "_date")
        if name.endswith(suffix)
    )
    delete_candidates = [
        field.column_name
        for field in fields
        if field.column_comment_zh and "删除" in normalize_comment(field.column_comment_zh)
    ]
    abbreviations = {
        english: short
        for english, short in COMMON_ABBREVIATIONS.items()
        if any(short in name.split("_") for name in english_names)
    }

    stats = {
        "field_count": len(english_names),
        "snake_case_ratio": round(snake_case_ratio, 4),
        "boolean_prefixes": [item for item, _ in boolean_prefix_counter.most_common(3)],
        "id_suffixes": [item for item, _ in id_suffix_counter.most_common(3)],
        "datetime_suffixes": [item for item, _ in datetime_suffix_counter.most_common(3)],
        "delete_patterns": delete_candidates[:5],
        "sample_fields": [
            {
                "column_name": field.column_name,
                "comment_zh": field.column_comment_zh,
                "table_name": field.table_name,
            }
            for field in fields[:12]
        ],
    }
    if progress_callback is not None:
        progress_callback("llm_summary", "正在生成命名风格摘要", 80)
    summary, source = llm_gateway.summarize_style({"stats": stats, "abbreviations": abbreviations})
    if progress_callback is not None:
        progress_callback("completed", "风格分析完成", 100)
    return stats, abbreviations, summary, source
