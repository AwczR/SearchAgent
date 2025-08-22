import json
import os
from typing import List
from datetime import datetime
from app.schema import Workspace, Doc, SubGoal
from app.config import get_settings

def _path(ws_id: str) -> str:
    s = get_settings()
    return os.path.join(s.DATA_DIR, f"{ws_id}.json")

def load_ws(ws_id: str) -> Workspace:
    p = _path(ws_id)
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Workspace(**data)

def save_ws(ws: Workspace) -> None:
    ws.updated_at = datetime.utcnow()
    p = _path(ws.id)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(
            ws.model_dump(mode="json"),  # ✅ 用 Pydantic 的 JSON 模式
            f,
            ensure_ascii=False,
            indent=2,
        )
def add_docs(ws: Workspace, docs: List[Doc]) -> Workspace:
    ws.docs.extend(docs)
    return ws

def set_goal(ws: Workspace, goal: str) -> Workspace:
    ws.goal = goal
    return ws

def add_subgoals(ws: Workspace, subs: List[SubGoal]) -> Workspace:
    ws.sub_goals.extend(subs)
    return ws