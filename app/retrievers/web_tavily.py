from typing import List
from tavily import TavilyClient
from app.schema import Doc
from app.config import get_settings

class WebRetriever:
    def __init__(self):
        s = get_settings()
        if not s.TAVILY_API_KEY:
            raise RuntimeError("TAVILY_API_KEY missing")
        self.client = TavilyClient(api_key=s.TAVILY_API_KEY)

    def search(self, query: str, k: int = 8) -> List[Doc]:
        res = self.client.search(query=query, max_results=k, include_raw_content=True, include_answer=False)
        docs: List[Doc] = []
        for i, item in enumerate(res.get("results", [])):
            content = item.get("raw_content") or item.get("content") or ""
            docs.append(Doc(
                title=item.get("title") or "",
                url=item.get("url") or "",
                content=content,
                source="tavily",
                meta={"score": item.get("score"), "position": i}
            ))
        return docs