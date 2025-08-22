# app/agents/agent1_plan.py
from app.schema import Workspace, Decision, SubGoal
from langchain_core.prompts import ChatPromptTemplate
from app.llm.chat_sf import get_chat
from app.llm.stream import stream_json

PLAN_SCHEMA = {
    "name": "plan_decision",
    "schema": {
        "type": "object",
        "properties": {
            "need_more": {"type": "boolean"},
            "sub_goals": {"type": "array", "items": {"type": "string"}, "maxItems": 5}
        },
        "required": ["need_more", "sub_goals"],
        "additionalProperties": False
    }
}
_SYS = ""
_USER = """严格按 JSON Schema 输出，仅输出一个 JSON 对象。
任务：根据当前 Workspace，先判断是否需要更多资料；如需要，生成多条【可一次互联网检索完成（one-shot）】的子目标查询，写入 sub_goals。

约束（必须全部遵守）：
- 语言：中文。
- 每条 sub_goal 是【完整可直接粘贴到搜索引擎】的查询串。
- 自包含：不得使用“这/上述/该问题”等指代；不依赖对话上下文。
- 原子性：一次查询可获得主要答案或高置信入口；禁止多跳推理、链式步骤、合并多个问题。
- 具体可判定：限定时间、地域、对象、版本或数据来源；避免宽泛词（如“最新”“影响”等）。
- 可检索性增强：必要时加入运算符或提示词，如 site:、filetype:、intitle:、OR、精确短句引号等。
- 明确信息类型：可加“定义/对比/教程/API/价格/评测/论文/代码”等词。
- 长度 ≤ 120 字；不含标点收尾要求外的多余符号；不加解释或标签。
- 去重与解耦：子目标之间不重复；若主题不同则拆为多条。
- 需要对比的信息，应当分别查询数据，而不是直接查询A与B的数据对比

need_more 判定准则（用于输出 need_more 的布尔值）：
- 若 Docs count 为 0，或 Goal 含多义名词/缺少时间地域/需外部事实核验/需权威来源，则 need_more=true；
- 若现有文档能直接回答且无需外部验证，则 need_more=false。

可用上下文：
Goal: {goal}
Docs count: {n_docs}
只输出 JSON。"""

def decide_and_plan(llm=None, ws: Workspace = None) -> Decision:
    print("[Agent1.stream] 规划与决策：")
    llm = llm or get_chat()
    prompt = ChatPromptTemplate.from_messages([("system", _SYS), ("user", _USER)])
    data = stream_json(prompt.format_messages(goal=ws.goal or ws.question, n_docs=len(ws.docs)),
                       schema=PLAN_SCHEMA, llm=llm)
    subs = [SubGoal(query=q) for q in data.get("sub_goals", []) if q.strip()]
    return Decision(need_more=bool(data.get("need_more", False)), sub_goals=subs)