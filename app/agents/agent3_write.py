# app/agents/agent3_write.py
from typing import List
from langchain_core.prompts import ChatPromptTemplate
from app.llm.chat_sf import get_chat
from app.llm.stream import stream_json
from app.schema import Workspace, Doc

# 兼容两种格式：int 或 {"doc_index": int, ...}
ANSWER_SCHEMA = {
    "name": "final_answer",
    "schema": {
        "type": "object",
        "properties": {
            "answer": {"type": "string", "minLength": 1},
            "citations": {
                "type": "array",
                "items": {
                    "oneOf": [
                        {"type": "integer", "minimum": 0},
                        {
                            "type": "object",
                            "properties": {
                                "doc_index": {"type": "integer", "minimum": 0},
                                "evidence": {"type": "string"}
                            },
                            "required": ["doc_index"],
                            "additionalProperties": False
                        }
                    ]
                }
            }
        },
        "required": ["answer", "citations"],
        "additionalProperties": False
    }
}

_SYS = ""
_USER = (
    """
        你是一个严谨的学术研究写作者，擅长撰写高水平论文。  
        请你根据以下要求写作：  

        1. 保持学术写作风格：  
        - 语言正式、客观、中立  
        - 逻辑清晰，论点有证据支持  
        - 段落结构完整，每段有中心思想  
        - 内容饱满丰富

        2. 内容要素：  
        - 有一个明确的研究主题或问题   
        - 用最适合主题的方式去书写  

        3. 写作要求：  
        - 必须分段，层次分明    
        - 语言流畅，避免口语化  
         """
    "严格按 JSON Schema 输出，answer 为成文论文。citations 使用0基索引。"
    "主问题：{q}\n目标：{g}\n\n资料（带索引，从0计数）：\n{ctx}\n\n请输出 answer 与 citations。"
)

def _mk_context(docs: List[Doc], max_chars: int = 1000) -> str:
    rows = []
    for i, d in enumerate(docs):
        head = d.title or d.url or d.id
        body = (d.content or "")[:max_chars].replace("\n", " ")
        rows.append(f"[{i}] {head}\n{body}")
    return "\n\n".join(rows)

def _normalize_citations(cites, n_docs: int) -> list[int]:
    if not isinstance(cites, list):
        return []
    out = []
    for c in cites:
        if isinstance(c, int):
            idx = c
        elif isinstance(c, dict):
            idx = c.get("doc_index")
        else:
            continue
        if isinstance(idx, int) and 0 <= idx < n_docs:
            out.append(idx)
    return sorted(dict.fromkeys(out))

def _format_references(docs: List[Doc], idxs: List[int]) -> str:
    lines = []
    for i in idxs:
        d = docs[i]
        url = (d.url or "").strip()
        if not url:
            continue
        title = (d.title or d.id or "untitled").strip()
        lines.append(f"- [{i+1}] {title} -> {url}")
    return "\n".join(lines)

def _attach_citations_and_sources(answer: str, cites_any, docs: List[Doc]) -> str:
    idxs = _normalize_citations(cites_any, len(docs))
    if not idxs:
        return answer
    # 文内标注
    marks = " ".join(f"[{i+1}]" for i in idxs)
    out = f"{answer}\n\n参考：{marks}"
    # 追加来源网址
    refs = _format_references(docs, idxs)
    if refs:
        out += f"\n\n来源：\n{refs}"
    return out

def compose_answer(llm=None, ws: Workspace = None) -> str:
    print("[Agent3.stream] 生成最终回答：")
    llm = llm or get_chat()
    ctx = _mk_context(ws.docs)
    prompt = ChatPromptTemplate.from_messages([("system", _SYS), ("user", _USER)])
    data = stream_json(
        prompt.format_messages(q=ws.question, g=ws.goal or "", ctx=ctx),
        schema=ANSWER_SCHEMA,
        llm=llm
    )
    ans = (data.get("answer") or "").strip()
    cites = data.get("citations") or []
    return _attach_citations_and_sources(ans, cites, ws.docs) if ans else "（无有效回答）"