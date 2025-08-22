# app/pipelines/main_loop.py
from typing import List, Tuple, Optional, Set
from app.schema import Workspace, Doc
from app.workspace import save_ws, set_goal, add_docs, add_subgoals
from app.llm.chat_sf import get_chat
from app.agents.agent0_intake import rewrite_goal, gen_clarifying_questions
from app.agents.agent1_plan import decide_and_plan
from app.agents.agent2_filter import select_docs
from app.agents.agent3_write import compose_answer
from app.retrievers.web_tavily import WebRetriever
from app.config import get_settings


def _print_docs(tag: str, docs: List[Doc], limit: int = 5) -> None:
    print(f"\n[{tag}] 共 {len(docs)} 条，前{min(limit, len(docs))}条：")
    for i, d in enumerate(docs[:limit]):
        title = d.title or d.url or d.id
        url = d.url or ""
        snippet = (d.content[:160] + "…") if d.content and len(d.content) > 160 else (d.content or "")
        print(f"  [{i}] {title} -> {url}\n      {snippet}")


def _sig(d: Doc) -> str:
    """用于去重的签名"""
    return f"{(d.url or '').strip()}||{(d.title or '').strip()}"


def start_intake(query: str) -> Tuple[Workspace, list[str]]:
    """阶段1：仅产生澄清问题，不前进。"""
    llm = get_chat()
    ws = Workspace(question=query)
    print(f"[Pipeline] 原始问题: {ws.question}")
    qs = gen_clarifying_questions(llm, ws.question)
    print(f"[Agent0] 澄清问题: {qs}")
    save_ws(ws)
    return ws, qs


def continue_after_answers(
    ws: Workspace,
    answers: List[str],
    max_loops: int = 3,       # 防止无限循环
    per_goal_k: Optional[int] = None
) -> Tuple[Workspace, str]:
    """阶段2：收到用户回答后进入循环：规划→检索→筛选，直至不需要更多资料。"""
    llm = get_chat()
    s = get_settings()
    retriever = WebRetriever()
    k = per_goal_k or s.DEFAULT_TOPK

    # 改写目标
    print("[Agent0] 改写目标中…")
    goal = rewrite_goal(llm, ws.question, answers)
    print(f"[Agent0] 改写后的目标: {goal}")
    ws = set_goal(ws, goal)
    save_ws(ws)

    # 循环补数
    seen: Set[str] = {_sig(d) for d in ws.docs}
    for loop_id in range(1, max_loops + 1):
        print(f"\n===== 循环回合 {loop_id} =====")

        print("[Agent1] 规划与决策中…")
        decision = decide_and_plan(llm, ws)
        print(f"[Agent1] need_more={decision.need_more} 子目标={[sg.query for sg in decision.sub_goals]}")

        if not decision.need_more or not decision.sub_goals:
            print("[Agent1] 判定无需新增资料。")
            break

        ws = add_subgoals(ws, decision.sub_goals)

        new_docs_cnt = 0
        for sg in decision.sub_goals:
            print(f"\n[Agent1] 执行子目标: {sg.query}")
            raw = retriever.search(sg.query, k=k)
            # 去重（原始检索）
            raw_unique = [d for d in raw if _sig(d) not in seen]
            _print_docs("Retriever 原始结果", raw_unique)

            kept = select_docs(llm, ws.question, sg.query, raw_unique, top_k=min(6, k))
            _print_docs("Agent2 保留结果", kept)

            # 去重（保留后）
            kept = [d for d in kept if _sig(d) not in seen]
            for d in kept:
                seen.add(_sig(d))
            if kept:
                ws = add_docs(ws, kept)
                new_docs_cnt += len(kept)

        save_ws(ws)

        # 若本回合没有新增资料，提前退出，防止空转
        if new_docs_cnt == 0:
            print("[Loop] 本回合未新增任何资料，提前结束循环。")
            break

    # 生成回答
    print("\n[Agent3] 生成最终回答中…")
    answer = compose_answer(llm, ws)
    print("[Agent3] 回答生成完毕。")
    save_ws(ws)

    print("\n=== 最终回答 ===\n", answer)
    return ws, answer


def run_once(
    query: Optional[str] = None,
    user_answers: Optional[List[str]] = None,
    existing_ws: Optional[Workspace] = None,
):
    """
    兼容两种用法：
    - 仅传 query：只做 intake，返回 (ws, None)
    - 传 existing_ws + user_answers：继续执行循环，返回 (ws, answer)
    - 传 query + user_answers（旧用法）：内部创建新 ws 并继续执行
    """
    if existing_ws and user_answers:
        return continue_after_answers(existing_ws, user_answers)

    if query and not user_answers:
        ws, qs = start_intake(query)
        print("[Agent0] 请先收集用户回答，再调用 continue_after_answers(ws, answers)。")
        return ws, None

    if query and user_answers:
        ws = Workspace(question=query)
        return continue_after_answers(ws, user_answers)

    raise ValueError("用法错误：请传入 (query) 或 (existing_ws, user_answers) 或 (query, user_answers)。")