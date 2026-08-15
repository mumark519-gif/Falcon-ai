from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()

def env_bool(name: str, default: bool=False) -> bool:
    v=os.getenv(name)
    return default if v is None else v.strip().lower() in {"1","true","yes","on"}

@dataclass(frozen=True)
class FalconSettings:
    app_name: str = os.getenv("APP_NAME","Falcon AI")
    env: str = os.getenv("APP_ENV","development")
    secret_key: str = os.getenv("SECRET_KEY","change-me")
    database_url: str = os.getenv("DATABASE_URL","sqlite:///./falcon.db")
    default_provider: str = os.getenv("AI_PROVIDER","openai")
    openai_api_key: str|None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL","gpt-5-mini")
    anthropic_api_key: str|None = os.getenv("ANTHROPIC_API_KEY")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL","claude-sonnet-4-5")
    kimi_api_key: str|None = os.getenv("KIMI_API_KEY")
    kimi_model: str = os.getenv("KIMI_MODEL","kimi-k2")
    google_api_key: str|None = os.getenv("GOOGLE_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL","gemini-2.5-flash")
    openai_compatible_base_url: str|None = os.getenv("OPENAI_COMPATIBLE_BASE_URL")
    openai_compatible_api_key: str|None = os.getenv("OPENAI_COMPATIBLE_API_KEY")
    openai_compatible_model: str|None = os.getenv("OPENAI_COMPATIBLE_MODEL")
    tavily_api_key: str|None = os.getenv("TAVILY_API_KEY")
    github_token: str|None = os.getenv("FALCON_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")
    github_repository: str|None = os.getenv("FALCON_GITHUB_REPOSITORY") or os.getenv("GITHUB_REPOSITORY")
    github_api_url: str = os.getenv("GITHUB_API_URL","https://api.github.com")
    cors_origins: str = os.getenv("CORS_ORIGINS","*")
    max_context_tokens: int = int(os.getenv("MAX_CONTEXT_TOKENS","12000"))
    enable_autonomy: bool = env_bool("FALCON_ENABLE_AUTONOMY", True)
    require_write_approval: bool = env_bool("FALCON_REQUIRE_WRITE_APPROVAL", True)
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    ai_max_retries: int = int(os.getenv("AI_MAX_RETRIES", "3"))
    ai_retry_delay: float = float(os.getenv("AI_RETRY_DELAY", "2.0"))
    ai_timeout: float = float(os.getenv("AI_TIMEOUT", "60.0"))

settings = FalconSettings()
