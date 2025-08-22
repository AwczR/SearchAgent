from typing import Iterable, Dict, Any, Optional
from openai import OpenAI
from app.config import get_settings

def stream_reason_and_answer(
    messages: Iterable[Dict[str, Any]],
    model: Optional[str] = None,
    max_tokens_reasoning: int = 4096,
    temperature: float = 0.0,
) -> str:
    """
    同时流式打印 reasoning_content（<think>）与最终 content。
    返回最终 content 文本。
    依赖：SILICONFLOW_BASE_URL, SILICONFLOW_API_KEY 在 .env 中设置。
    """
    s = get_settings()
    client = OpenAI(api_key=s.SF_API_KEY, base_url=s.SF_BASE_URL)
    mdl = model or s.SF_CHAT_MODEL

    print("[stream] model =", mdl)
    print("[stream] reasoning ...")
    final_text = []

    # 关键点：传 max_tokens_reasoning，推理模型才会产出 reasoning_content
    # 文档字段名：max_tokens_reasoning（用于推理token上限）与标准 chat/completions 流式协议。 [oai_citation:2‡docs.siliconflow.com](https://docs.siliconflow.com/cn/api-reference/chat-completions/chat-completions?utm_source=chatgpt.com)
    with client.chat.completions.stream.create(
        model=mdl,
        messages=list(messages),
        temperature=temperature,
        stream=True,
        max_tokens_reasoning=max_tokens_reasoning,
    ) as stream:
        for event in stream:
            # 推理增量
            if event.type == "reasoning.delta":
                chunk = event.delta or {}
                rc = chunk.get("reasoning_content") or ""
                if rc:
                    print(rc, end="", flush=True)
            # 最终推理结束
            elif event.type == "reasoning.completed":
                print("\n[stream] reasoning done.\n")
            # 可见回答增量
            elif event.type == "content.delta":
                txt = event.delta.get("content", "")
                if txt:
                    print(txt, end="", flush=True)
                    final_text.append(txt)
            # 回答结束
            elif event.type == "content.completed":
                print("\n[stream] content done.\n")
            # 其它事件类型忽略

    return "".join(final_text)