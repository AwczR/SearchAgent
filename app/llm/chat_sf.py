from langchain_openai import ChatOpenAI
from app.config import get_settings

def get_chat(model: str | None = None) -> ChatOpenAI:
    s = get_settings()
    return ChatOpenAI(
        model=model or s.SF_CHAT_MODEL,
        api_key=s.SF_API_KEY.strip(),
        base_url=s.SF_BASE_URL.strip(),   # 一定要传
        temperature=s.LLM_TEMPERATURE,
    )