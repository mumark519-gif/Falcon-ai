"""Public API schemas for Falcon AI.

The package is the single canonical schema namespace.  Keeping the public
request/response models here avoids the historical collision between
``app/schemas.py`` and the ``app/schemas/`` package.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class User(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    email: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str


from .agent import AgentRequest

__all__ = ["User", "Token", "AgentRequest"]
