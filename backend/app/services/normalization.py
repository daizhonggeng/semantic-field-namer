from __future__ import annotations

import re
from difflib import SequenceMatcher

ZH_SYNONYMS = {
    "编号": "id",
    "标识": "id",
    "ID": "id",
    "Id": "id",
    "id": "id",
    "手机号": "手机号码",
    "联系电话": "手机号码",
    "电话号码": "手机号码",
    "删除标记": "删除标志",
    "删除标识": "删除标志",
    "建立时间": "创建时间",
    "新增时间": "创建时间",
}

ENGLISH_HINTS = {
    "用户": "user",
    "名称": "name",
    "状态": "status",
    "描述": "description",
    "备注": "remark",
    "电话": "mobile",
    "手机": "mobile",
    "号码": "no",
    "删除": "delete",
    "标志": "flag",
    "创建": "create",
    "更新时间": "updated_at",
    "创建时间": "created_at",
    "时间": "time",
    "日期": "date",
    "地址": "address",
    "类型": "type",
    "编码": "code",
    "批次": "batch",
    "排序": "sort",
    "数量": "qty",
}


def normalize_comment(comment: str) -> str:
    text = re.sub(r"[\s_\-]+", "", comment.strip())
    for old, new in ZH_SYNONYMS.items():
        text = text.replace(old, new)
    return text.lower()


def snake_case(name: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "_", name)
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text.lower()


def similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, normalize_comment(left), normalize_comment(right)).ratio()


def simple_translate(comment: str) -> str:
    normalized = normalize_comment(comment)
    tokens: list[str] = []
    for chinese, english in ENGLISH_HINTS.items():
        if chinese in comment:
            tokens.append(english)
    if not tokens:
        digest = abs(hash(normalized)) % 10_000
        tokens = ["field", str(digest)]
    return snake_case("_".join(tokens))
