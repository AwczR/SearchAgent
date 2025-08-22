# app/llm/stream.py
import json
from typing import Optional, Dict, Any, Iterable, List
from app.llm.chat_sf import get_chat
from langchain_core.messages import BaseMessage
from app.config import get_settings

def _safe_json(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        s = text[text.find("{"): text.rfind("}") + 1]
        return json.loads(s)

def stream_text(messages, response_format=None, llm=None) -> str:
    llm = llm or get_chat()
    s = get_settings()

    # A. 显示思考时开启返回开关，并给预算
    if getattr(s, "SHOW_THINK", False):
        llm = llm.bind(
            extra_body={
                "include_reasoning": True,      # 要求服务端下发思考内容
                "thinking_budget": 1024         # 控制思考长度
            }
        )

    # B. 展示思考时不要绑 JSON 格式
    if response_format and not getattr(s, "SHOW_THINK", False):
        llm = llm.bind(response_format=response_format)

    buf = []
    for chunk in llm.stream(messages):
        if getattr(s, "SHOW_THINK", False):
            rc = (getattr(chunk, "additional_kwargs", {}) or {}).get("reasoning_content") or ""

            # 兜底：从原始增量里拿
            if not rc:
                meta = getattr(chunk, "response_metadata", {}) or {}
                delta = (meta.get("delta") or {})
                if not delta:
                    raw = meta.get("raw") or {}
                    choices = raw.get("choices") or []
                    delta = (choices[0].get("delta") if choices else {}) or {}
                rc = delta.get("reasoning_content") or ""

            if rc:
                print(rc, end="", flush=True)

        part = getattr(chunk, "content", "") or ""
        if part:
            print(part, end="", flush=True)
            buf.append(part)

    print()
    return "".join(buf)

def stream_json(messages: Iterable[BaseMessage], schema: Optional[Dict[str, Any]] = None, llm=None) -> dict:
    text = stream_text(
        messages,
        response_format=({"type": "json_schema", "json_schema": schema} if schema else {"type": "json_object"}),
        llm=llm,
    )
    return _safe_json(text)