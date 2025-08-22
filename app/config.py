import os
from functools import lru_cache
from dotenv import load_dotenv, find_dotenv

# 强制从当前工作目录向上查找 .env，并覆盖系统环境
_DOTENV_PATH = find_dotenv(filename=".env", usecwd=True)
if not _DOTENV_PATH:
    print("[config] WARN: .env not found from CWD")
else:
    print(f"[config] load .env -> {_DOTENV_PATH}")
    load_dotenv(_DOTENV_PATH, override=True)  # 关键：override=True

class Settings:
    SF_API_KEY: str = os.getenv("SILICONFLOW_API_KEY", "").strip()
    SF_BASE_URL: str = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1").strip()
    SF_CHAT_MODEL: str = os.getenv("SF_CHAT_MODEL", "deepseek-ai/DeepSeek-V3").strip()
    SF_RERANK_MODEL: str = os.getenv("SF_RERANK_MODEL", "Qwen/Qwen3-Reranker-8B").strip()
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "").strip()
    DEFAULT_TOPK: int = int(os.getenv("DEFAULT_TOPK", "8"))
    DATA_DIR: str = os.getenv("DATA_DIR", "data").strip()
    SHOW_THINK: bool = os.getenv("SHOW_THINK", "1") in ("1", "true", "True")
@lru_cache()
def get_settings() -> "Settings":
    s = Settings()
    os.makedirs(s.DATA_DIR, exist_ok=True)
    # 启动时打印关键变量前缀用于核验
    print("[config] BASE_URL:", s.SF_BASE_URL)
    print("[config] KEY_PREFIX:", (s.SF_API_KEY[:6] + "***") if s.SF_API_KEY else "EMPTY")
    return s