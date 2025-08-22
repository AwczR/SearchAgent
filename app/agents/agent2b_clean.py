# app/agents/agent2b_clean.py
from typing import List
from langchain_core.prompts import ChatPromptTemplate
from app.llm.chat_sf import get_chat
from app.llm.stream import stream_text
from app.schema import Doc

_SYS = ""
_USER = """你是文本清洗器。对给定文本做“最小但有效”的清洗，仅输出清洗后的纯文本：
- 删除：乱码、无意义字符块、导航/广告/版权尾注、冗余页眉页脚、过长重复行、base64/十六进制大段、无内容表格框线
- 保留：正文要点、定义、结论、数据、公式（用纯文本保留）、标题与小标题、列表项
- 规整：去重与空白，合并破碎的句子，保持段落可读；保留层级语义（标题→段落→列表）
- 禁止：新增编造信息；解释说明；任何 JSON 或标记包装
待清洗文本：
{content}"""

def clean_text(llm=None, content: str = "") -> str:
    llm = llm or get_chat()
    prompt = ChatPromptTemplate.from_messages([("system", _SYS), ("user", _USER)])
    out = stream_text(prompt.format_messages(content=content), llm=llm)
    return out.strip()

def clean_docs(llm=None, docs: List[Doc] | None = None) -> List[Doc]:
    if not docs:
        return []
    llm = llm or get_chat()
    res: List[Doc] = []
    for d in docs:
        try:
            c = clean_text(llm=llm, content=d.content or "")
            d.content = c
            d.meta = dict(d.meta or {})
            d.meta["cleaned"] = True
        except Exception as e:
            d.meta = dict(d.meta or {})
            d.meta["clean_error"] = str(e)
        res.append(d)
    return res