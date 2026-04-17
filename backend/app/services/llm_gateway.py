from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.services.ai_config_service import get_active_ai_config
from app.services.normalization import simple_translate

STYLE_SUMMARY_PROMPT = """你是数据库字段命名风格分析师。
只根据输入的统计信息和样本，提炼命名军规。
输出必须简短、务实、面向字段命名，不要编造不存在的规范。
"""

FIELD_NAMING_PROMPT = """你是数据库字段命名专家。
任务：为一批中文字段注释生成英文字段名。

强约束：
1. 只能输出 snake_case。
2. 必须尽量复用既有风格、缩写偏好和参考字段。
3. 如果参考中已存在语义接近的命名模式，优先沿用该模式。
4. 禁止输出 CamelCase、拼音、空格和解释性文本。
5. 必须处理批量内重名风险。
6. 只输出符合 JSON Schema 的内容。
"""


class StyleSummaryResult(BaseModel):
    summary: str


class FieldCandidate(BaseModel):
    comment_zh: str
    candidate_name: str
    confidence: float = Field(ge=0, le=1)
    based_on: str | None = None
    is_new_term: bool = False
    rationale: str | None = None


class FieldBatchResult(BaseModel):
    items: list[FieldCandidate]


class LlmGateway:
    def __init__(self) -> None:
        self.config = get_active_ai_config()
        self._client = None

    def _get_client(self):  # noqa: ANN202
        if self._client is not None:
            return self._client
        if not (self.config.api_key and self.config.base_url):
            return None
        from openai import OpenAI

        self._client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout_seconds,
            max_retries=self.config.max_retries,
        )
        return self._client

    def health_check(self) -> dict[str, Any]:
        checked_at = datetime.now(UTC)
        if not self.config.api_key:
            return self._health_payload(False, False, False, True, checked_at, "OPENAI_API_KEY is missing")
        if not self.config.base_url:
            return self._health_payload(False, False, False, True, checked_at, "OPENAI_BASE_URL is missing")
        client = self._get_client()
        try:
            response = client.responses.create(
                model=self.config.model,
                input="Reply with ok",
                max_output_tokens=5,
                timeout=min(self.config.timeout_seconds, 10),
            )
            _ = getattr(response, "output_text", "") or "ok"
            return self._health_payload(True, True, True, False, checked_at, None)
        except Exception as exc:
            return self._health_payload(True, False, True, True, checked_at, str(exc))

    def summarize_style(self, payload: dict[str, Any]) -> tuple[str, str]:
        client = self._get_client()
        if client is None:
            return self._heuristic_style_summary(payload), "heuristic"
        try:
            response = client.responses.parse(
                model=self.config.model,
                instructions=STYLE_SUMMARY_PROMPT,
                input=json.dumps(payload, ensure_ascii=False),
                text_format=StyleSummaryResult,
                timeout=self.config.timeout_seconds,
            )
            return response.output_parsed.summary, "llm"
        except Exception:
            return self._heuristic_style_summary(payload), "heuristic"

    def generate_field_names(self, payload: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
        client = self._get_client()
        if client is None:
            return self._fallback_candidates(payload), False
        try:
            response = client.responses.parse(
                model=self.config.model,
                instructions=FIELD_NAMING_PROMPT,
                input=json.dumps(payload, ensure_ascii=False),
                text_format=FieldBatchResult,
                timeout=self.config.timeout_seconds,
            )
            return [item.model_dump() for item in response.output_parsed.items], True
        except Exception:
            try:
                response = client.responses.create(
                    model=self.config.model,
                    instructions=FIELD_NAMING_PROMPT,
                    input=json.dumps(payload, ensure_ascii=False),
                    timeout=self.config.timeout_seconds,
                )
                parsed = json.loads(response.output_text)
                return parsed.get("items", []), True
            except Exception:
                return self._fallback_candidates(payload), False

    def _heuristic_style_summary(self, payload: dict[str, Any]) -> str:
        stats = payload.get("stats", {})
        abbreviations = payload.get("abbreviations", {})
        boolean_prefixes = ", ".join(stats.get("boolean_prefixes", [])) or "无明显统一前缀"
        id_suffixes = ", ".join(stats.get("id_suffixes", [])) or "以 _id 为主"
        abbreviations_text = ", ".join(f"{k}->{v}" for k, v in abbreviations.items()) or "无明显缩写偏好"
        return (
            f"字段整体以 snake_case 为主。布尔字段常见前缀：{boolean_prefixes}。"
            f"编号/主键命名偏好：{id_suffixes}。常见缩写：{abbreviations_text}。"
        )

    def _fallback_candidates(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        items = []
        for field in payload.get("items", []):
            items.append(
                {
                    "comment_zh": field["comment_zh"],
                    "candidate_name": simple_translate(field["comment_zh"]),
                    "confidence": 0.45,
                    "based_on": "heuristic-fallback",
                    "is_new_term": True,
                    "rationale": "LLM unavailable, used local fallback translator",
                }
            )
        return items

    def _health_payload(
        self,
        configured: bool,
        reachable: bool,
        model_checked: bool,
        fallback_needed: bool,
        checked_at: datetime,
        error: str | None,
    ) -> dict[str, Any]:
        return {
            "configured": configured,
            "reachable": reachable,
            "model_checked": model_checked,
            "fallback_needed": fallback_needed,
            "base_url": self.config.base_url,
            "source_name": self.config.source_name,
            "provider_type": self.config.provider_type,
            "model": self.config.model,
            "checked_at": checked_at,
            "error": error,
        }
