from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
import uuid

def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

class Doc(BaseModel):
    id: str = Field(default_factory=lambda: _id("doc"))
    title: Optional[str] = None
    url: Optional[str] = None
    content: str
    score: Optional[float] = None
    source: Optional[str] = None
    meta: Dict = Field(default_factory=dict)

class SubGoal(BaseModel):
    id: str = Field(default_factory=lambda: _id("sub"))
    query: str
    status: str = "pending"

class Workspace(BaseModel):
    id: str = Field(default_factory=lambda: _id("ws"))
    question: str
    goal: Optional[str] = None
    docs: List[Doc] = Field(default_factory=list)
    sub_goals: List[SubGoal] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Decision(BaseModel):
    need_more: bool
    sub_goals: List[SubGoal] = Field(default_factory=list)