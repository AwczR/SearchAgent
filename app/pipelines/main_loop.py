# app/pipelines/main_loop.py
from typing import List, Tuple
from app.schema import Workspace, Doc, SubGoal, Decision
from app.workspace import save_ws, add_docs, set_goal, add_subgoals
from app.agents.agent0_intake import gen_clarifying_questions, rewrite_goal
from app.agents.agent1_plan import decide_and_plan
from app.agents.agent2_filter import select_docs
from app.agents.agent2b_clean import clean_docs   # ← 新增导入
from app.agents.agent3_write import compose_answer
from app.retrievers.web_tavily import WebRetriever
from app.config import get_settings

def _init_ws(query: str) -> Workspace:
    ws = Workspace(question=query)
    save_ws(ws)
    return ws

def start_intake(query: str) -> Tuple[Workspace, List[str]]:
    ws = _init_ws(query)
    qs = gen_clarifying_questions(query=query, k=3)
    save_ws(ws)
    return ws, qs

def _gather_more(ws: Workspace, dec: Decision, k: int = 8) -> Workspace:
    try:
        retr = WebRetriever()
    except Exception:
        return ws
    all_new: List[Doc] = []
    for sg in dec.sub_goals:
        all_new.extend(retr.search(query=sg.query, k=k))
    if all_new:
        ws = add_docs(ws, all_new)
        save_ws(ws)
    return ws

def _filter_then_clean(ws: Workspace, query: str, subquery: str | None = None, top_k: int = 8) -> List[Doc]:
    if not ws.docs:
        return []
    # 保持原有行为：直接用 agent2 在 ws.docs 上筛选
    kept = select_docs(query=query, subquery=subquery or query, docs=ws.docs, top_k=top_k)
    # 新增最小步骤：对保留文档做逐条 LLM 清洗，覆盖 content
    cleaned = clean_docs(docs=kept)
    return cleaned

def continue_after_answers(ws: Workspace, answers: str) -> Tuple[Workspace, str]:
    goal = rewrite_goal(query=ws.question, user_answers=[answers])
    ws = set_goal(ws, goal)

    dec = decide_and_plan(ws=ws)
    ws = add_subgoals(ws, dec.sub_goals)
    save_ws(ws)

    if dec.need_more:
        ws = _gather_more(ws, dec, k=get_settings().DEFAULT_TOPK)

    subq = dec.sub_goals[0].query if dec.sub_goals else ws.goal or ws.question
    kept_cleaned = _filter_then_clean(ws, query=ws.question, subquery=subq, top_k=get_settings().DEFAULT_TOPK)

    if kept_cleaned:
        ws.docs = kept_cleaned
        save_ws(ws)

    answer = compose_answer(ws=ws)
    return ws, answer