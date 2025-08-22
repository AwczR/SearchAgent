# app/agents/agent3_write.py
from __future__ import annotations
from typing import List, Tuple
from langchain_core.prompts import ChatPromptTemplate
from app.llm.chat_sf import get_chat
from app.llm.stream import stream_text
from app.schema import Workspace, Doc

_SYS = ""
_USER = """你将基于“候选资料片段”回答“用户问题”。要求：
- 直接给出答案，不要解释流程。
- 不要在正文里写“参考文献/来源/链接”等字样。
- 不要在正文里输出 URL，正文结束后我会自动附上来源列表。

用户问题：
{question}

若有目标：
{goal}

候选资料片段（可能已被清洗，仅供作答，不要原样粘贴长段）：
{contexts}
"""

def _mk_context(docs: List[Doc], max_chars_per_doc: int = 1200, max_docs: int = 8) -> Tuple[str, List[Doc]]:
    """把文档裁剪成可读片段，并返回用于展示的 doc 列表（保持顺序、去重 URL）"""
    seen = set()
    ordered: List[Doc] = []
    for d in docs:
        u = (d.url or "").strip()
        key = u or d.id
        if key in seen:
            continue
        seen.add(key)
        ordered.append(d)
        if len(ordered) >= max_docs:
            break

    lines = []
    for i, d in enumerate(ordered, 1):
        title = d.title or (d.url or "untitled")
        url = d.url or "(no url)"
        body = (d.content or "").strip()
        if len(body) > max_chars_per_doc:
            body = body[:max_chars_per_doc].rstrip() + " ..."
        lines.append(f"[{i}] {title}\nURL: {url}\n{body}\n")
    return "\n".join(lines), ordered

def _mk_refs(docs: List[Doc]) -> str:
    """生成参考来源列表，带 URL。只展示有 URL 的条目。"""
    refs = []
    seen = set()
    for i, d in enumerate(docs, 1):
        title = d.title or d.url or "untitled"
        url = (d.url or "").strip()
        if not url:
            continue
        if url in seen:
            continue
        seen.add(url)
        refs.append(f"{i}. [{title}]({url})")
    if not refs:
        return ""
    return "\n\n参考来源：\n" + "\n".join(refs) + "\n"

def compose_answer(llm=None, ws: Workspace | None = None) -> str:
    if ws is None:
        return "错误：Workspace 为空。"
    llm = llm or get_chat()

    # 组装上下文
    contexts, used_docs = _mk_context(ws.docs or [])

    # 调用 LLM 生成正文
    prompt = ChatPromptTemplate.from_messages([("system", _SYS), ("user", _USER)])
    body = stream_text(
        prompt.format_messages(
            question=ws.question,
            goal=ws.goal or "(未设定)",
            contexts=contexts or "(无)"
        ),
        llm=llm,
    ).strip()

    # 追加参考来源（只放 URL，不参与 LLM）
    refs = _mk_refs(used_docs)
    return body + (refs if refs else "")