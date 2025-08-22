# app/agents/agent2_filter.py
import json
from typing import List
from langchain.prompts import ChatPromptTemplate
from app.schema import Doc
from app.llm.chat_sf import get_chat
from app.llm.stream import stream_json

_SYS = (
    ""
)

_USER = (
    "你是资料筛选助手。"
    "输入是查询、子查询和候选资料列表。"
    "输出要保留的资料索引（JSON）。"
    "严格按 JSON Schema 输出，键名必须是 keep。"
    "若全部不保留，输出 {{\"keep\": []}}。"
    "主问题: {query}\n"
    "子问题: {subquery}\n\n"
    "候选资料:\n{catalog}\n\n"
    "请输出需要保留的资料索引号码。"
    "请只输出json"
)

KEEP_SCHEMA = {
    "name": "doc_selection",
    "schema": {
        "type": "object",
        "properties": {
            "keep": {
                "type": "array",
                "items": {"type": "integer", "minimum": 0},
                "minItems": 0,
                "maxItems": 20,
                "uniqueItems": True      # ✅ 索引唯一
            }
        },
        "required": ["keep"],
        "additionalProperties": False
    }
}


def _mk_catalog(docs: List[Doc]) -> str:
    """把候选文档整理成简洁的编号清单"""
    lines = []
    for i, d in enumerate(docs):
        title = d.title or d.url or "untitled"
        snippet = (d.content[:120] + "...") if len(d.content) > 120 else d.content
        lines.append(f"[{i}] {title}\n  {snippet}")
    return "\n".join(lines)


def select_docs(
    llm=None,
    query: str = "",
    subquery: str = "",
    docs: List[Doc] = None,
    top_k: int = 6
) -> List[Doc]:
    """调用 LLM 过滤候选文档"""
    if not docs:
        return []

    print("[Agent2.stream] 资料筛选：")
    llm = llm or get_chat()

    catalog = _mk_catalog(docs)
    prompt = ChatPromptTemplate.from_messages([("system", _SYS), ("user", _USER)])

    # 流式 JSON 解析
    data = stream_json(
        prompt.format_messages(query=query, subquery=subquery, catalog=catalog),
        schema=KEEP_SCHEMA,
        llm=llm,
    ) or {}

    # 兼容 LLM 返回 [] 的情况，并判断是否“明确选择0条”
    explicit_zero = False
    if isinstance(data, list):
        explicit_zero = (len(data) == 0)
        data = {"keep": [i for i in data if isinstance(i, int)]}
    elif isinstance(data, dict):
        if "keep" not in data:
            data = {"keep": []}
            explicit_zero = True
        else:
            k = data.get("keep", [])
            explicit_zero = isinstance(k, list) and len(k) == 0
    else:
        # 非法类型，视为解析失败
        data = {"keep": None}

    idxs = [i for i in (data.get("keep") or []) if isinstance(i, int) and 0 <= i < len(docs)]

    # ✅ 去重并保持顺序
    seen, uniq = set(), []
    for i in idxs:
        if i not in seen:
            seen.add(i)
            uniq.append(i)

    # 若明确选择0条 → 返回空；否则沿用原逻辑
    if uniq:
        kept = [docs[i] for i in uniq][:top_k]
    elif explicit_zero:
        kept = []
    else:
        kept = docs[:top_k]

    # 打印结果
    if not kept:
        print("  · 无保留文档")
    else:
        for i, d in enumerate(kept):
            print(f"  · {i+1}. {d.title or d.url}  -> {d.url}")

    return kept