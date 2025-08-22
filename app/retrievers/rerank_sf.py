from typing import List
import httpx
from app.schema import Doc
from app.config import get_settings

def rerank(query: str, docs: List[Doc], model: str | None = None) -> List[Doc]:
    """Call SiliconFlow rerank adapter (OpenAI-style). Assumes /v1/rerank."""
    s = get_settings()
    _model = model or s.SF_RERANK_MODEL
    payload = {
        "model": _model,
        "query": query,
        "documents": [d.content for d in docs],
        "return_documents": False
    }
    headers = {"Authorization": f"Bearer {s.SF_API_KEY}"}
    url = f"{s.SF_BASE_URL.rstrip('/')}/rerank"
    with httpx.Client(timeout=60) as client:
        r = client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
    # Expect scores aligned to input order or ranked indices
    scored = data.get("results") or []
    # results: [{"index": int, "relevance_score": float}, ...]
    ordered = []
    for item in sorted(scored, key=lambda x: x.get("relevance_score", 0), reverse=True):
        idx = item.get("index")
        d = docs[idx]
        d.score = float(item.get("relevance_score", 0))
        ordered.append(d)
    return ordered