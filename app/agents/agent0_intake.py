# app/agents/agent0_intake.py
from typing import List
from langchain_core.prompts import ChatPromptTemplate
from app.llm.chat_sf import get_chat
from app.llm.stream import stream_json

QS_SCHEMA = {
    "name": "clarify_questions",
    "schema": {
        "type": "object",
        "properties": {"questions": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 10}},
        "required": ["questions"],
        "additionalProperties": False
    }
}
GOAL_SCHEMA = {
    "name": "rewritten_goal",
    "schema": {
        "type": "object",
        "properties": {"goal": {"type": "string", "minLength": 1}},
        "required": ["goal"],
        "additionalProperties": False
    }
}

_QS_SYS = ""
_QS_USER = """严格按 JSON Schema 输出。
要求：
- 输出为一个 JSON 对象，禁止额外文字、注释、解释。
- 必须符合 Schema 定义，键名固定为 "questions"。
- 每个问题不超过25字，结尾不加标点。
- 问题不复述原题，要澄清范围、条件、限制、时间、地域、数据来源、评价标准、优先级。
给定问题：{q}
生成不超过{n}个澄清问题。"""
_RW_SYS = ""
_RW_USER = """严格按 JSON Schema 输出。
要求：
- 输出仅为一个 JSON 对象，禁止额外文字、注释、解释。
- 必须符合 Schema 定义，键名固定为 "goal"。
- 将原始问题与补充回答融合，改写为单句、清晰、可检索、可执行的目标。
- 吸收补充内容中的约束（时间、地域、输入输出格式、评价标准、数据来源、优先级）。
- 不虚构未提供的细节，若不足用中性占位词（如“指定数据集/时间范围”）。
- 目标不超过50字，避免口语和感叹。
原始问题：{q}
补充回答：
{a}
改写目标："""

def gen_clarifying_questions(llm=None, query: str = "", k: int = 3) -> List[str]:
    print("[Agent0.stream] 生成澄清问题：")
    llm = llm or get_chat()
    prompt = ChatPromptTemplate.from_messages([("system", _QS_SYS), ("user", _QS_USER)])
    data = stream_json(prompt.format_messages(q=query, n=k), schema=QS_SCHEMA, llm=llm)
    return data.get("questions", [])[:k]

def rewrite_goal(llm=None, query: str = "", user_answers: List[str] | None = None) -> str:
    print("[Agent0.stream] 改写目标：")
    llm = llm or get_chat()
    ans = "\n".join(user_answers or [])
    prompt = ChatPromptTemplate.from_messages([("system", _RW_SYS), ("user", _RW_USER)])
    data = stream_json(prompt.format_messages(q=query, a=ans), schema=GOAL_SCHEMA, llm=llm)
    return (data.get("goal") or query).strip()