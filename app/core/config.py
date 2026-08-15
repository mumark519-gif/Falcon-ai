"""Backward-compatible Falcon settings facade.

New code should prefer ``app.core.settings.settings`` and snake_case fields.
Older modules/tests in Falcon still use the original UPPER_CASE names, so this
facade intentionally exposes both without maintaining two configuration
sources.
"""
from __future__ import annotations

from app.core.settings import settings as _settings


class SettingsCompat:
    def __getattr__(self, name: str):
        mapping = {
            "APP_NAME": "app_name",
            "APP_ENV": "env",
            "DATABASE_URL": "database_url",
            "SECRET_KEY": "secret_key",
            "ACCESS_TOKEN_EXPIRE_MINUTES": "access_token_expire_minutes",
            "AI_PROVIDER": "default_provider",
            "AI_MAX_RETRIES": "ai_max_retries",
            "AI_RETRY_DELAY": "ai_retry_delay",
            "AI_TIMEOUT": "ai_timeout",
            "OPENAI_API_KEY": "openai_api_key",
            "OPENAI_MODEL": "openai_model",
            "GOOGLE_API_KEY": "google_api_key",
            "GEMINI_MODEL": "gemini_model",
            "TAVILY_API_KEY": "tavily_api_key",
            "ANTHROPIC_API_KEY": "anthropic_api_key",
            "ANTHROPIC_MODEL": "anthropic_model",
            "KIMI_API_KEY": "kimi_api_key",
            "KIMI_MODEL": "kimi_model",
        }
        target = mapping.get(name)
        if target is not None:
            return getattr(_settings, target)
        return getattr(_settings, name)


# Preserve the historical import contract: ``from app.core.config import settings``.
settings = SettingsCompat()
