from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    JSON,
)

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    username = Column(
        String,
        unique=True,
        index=True,
    )

    email = Column(
        String,
        unique=True,
        index=True,
        nullable=True,
    )

    password = Column(String)


class Chat(Base):
    __tablename__ = "chats"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    username = Column(
        String,
        index=True,
    )

    title = Column(
        String,
        default="New Chat",
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    username = Column(
        String,
        index=True,
    )

    chat_id = Column(
        Integer,
        ForeignKey("chats.id"),
    )

    role = Column(String)

    message = Column(String)

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )


class Memory(Base):
    __tablename__ = "memories"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    username = Column(
        String,
        index=True,
    )

    key = Column(
        String,
        index=True,
    )

    value = Column(String)

    category = Column(
        String,
        default="general",
    )

    importance = Column(
        Integer,
        default=5,
    )

    confidence = Column(
        Integer,
        default=100,
    )

    access_count = Column(
        Integer,
        default=0,
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

class MemoryEmbedding(Base):

    __tablename__ = "memory_embeddings"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    memory_id = Column(
        Integer,
        ForeignKey("memories.id"),
        nullable=False,
    )

    model = Column(
        String,
        nullable=False,
    )

    embedding = Column(
        JSON,
        nullable=False,
    )

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    owner_username = Column(String, nullable=False, index=True)
    plan = Column(String, nullable=False, default="free")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Membership(Base):
    __tablename__ = "memberships"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    username = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False, default="user")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    plan = Column(String, nullable=False, default="free")
    status = Column(String, nullable=False, default="active")
    provider_customer_id = Column(String, nullable=True)
    provider_subscription_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True, index=True)
    username = Column(String, nullable=False, index=True)
    provider = Column(String, nullable=True)
    model = Column(String, nullable=True)
    kind = Column(String, nullable=False, default="chat")
    tokens_in = Column(Integer, nullable=True)
    tokens_out = Column(Integer, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    username = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    key_prefix = Column(String, nullable=False, index=True)
    key_hash = Column(String, nullable=False, unique=True, index=True)
    revoked = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_used_at = Column(DateTime, nullable=True)


class AuditLogRecord(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True, index=True)
    username = Column(String, nullable=True, index=True)
    event = Column(String, nullable=False, index=True)
    details = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
