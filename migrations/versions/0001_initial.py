"""Initial Falcon schema.

Revision ID: 0001_initial
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("username", sa.String(), nullable=False), sa.Column("email", sa.String(), nullable=True), sa.Column("password", sa.String(), nullable=False))
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("organizations", sa.Column("id", sa.String(), primary_key=True), sa.Column("name", sa.String(), nullable=False), sa.Column("owner_username", sa.String(), nullable=False), sa.Column("plan", sa.String(), nullable=False, server_default="free"), sa.Column("created_at", sa.DateTime(), nullable=True))
    op.create_index("ix_organizations_owner_username", "organizations", ["owner_username"])
    op.create_table("chats", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("username", sa.String(), nullable=True), sa.Column("title", sa.String(), nullable=True), sa.Column("created_at", sa.DateTime(), nullable=True))
    op.create_index("ix_chats_id", "chats", ["id"])
    op.create_index("ix_chats_username", "chats", ["username"])
    op.create_table("conversations", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("username", sa.String(), nullable=True), sa.Column("chat_id", sa.Integer(), sa.ForeignKey("chats.id"), nullable=True), sa.Column("role", sa.String(), nullable=True), sa.Column("message", sa.String(), nullable=True), sa.Column("created_at", sa.DateTime(), nullable=True))
    op.create_index("ix_conversations_id", "conversations", ["id"])
    op.create_index("ix_conversations_username", "conversations", ["username"])
    op.create_table("memories", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("username", sa.String(), nullable=True), sa.Column("key", sa.String(), nullable=True), sa.Column("value", sa.String(), nullable=True), sa.Column("category", sa.String(), server_default="general"), sa.Column("importance", sa.Integer(), server_default="5"), sa.Column("confidence", sa.Integer(), server_default="100"), sa.Column("access_count", sa.Integer(), server_default="0"), sa.Column("created_at", sa.DateTime(), nullable=True), sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.create_index("ix_memories_id", "memories", ["id"])
    op.create_index("ix_memories_username", "memories", ["username"])
    op.create_index("ix_memories_key", "memories", ["key"])
    op.create_table("memory_embeddings", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("memory_id", sa.Integer(), sa.ForeignKey("memories.id"), nullable=False), sa.Column("model", sa.String(), nullable=False), sa.Column("embedding", sa.JSON(), nullable=False))
    op.create_index("ix_memory_embeddings_id", "memory_embeddings", ["id"])
    op.create_table("memberships", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("organization_id", sa.String(), sa.ForeignKey("organizations.id"), nullable=False), sa.Column("username", sa.String(), nullable=False), sa.Column("role", sa.String(), nullable=False, server_default="user"))
    op.create_index("ix_memberships_id", "memberships", ["id"])
    op.create_index("ix_memberships_organization_id", "memberships", ["organization_id"])
    op.create_index("ix_memberships_username", "memberships", ["username"])
    op.create_table("subscriptions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("organization_id", sa.String(), sa.ForeignKey("organizations.id"), nullable=False), sa.Column("plan", sa.String(), nullable=False, server_default="free"), sa.Column("status", sa.String(), nullable=False, server_default="active"), sa.Column("provider_customer_id", sa.String()), sa.Column("provider_subscription_id", sa.String()), sa.Column("created_at", sa.DateTime()), sa.Column("updated_at", sa.DateTime()))
    op.create_index("ix_subscriptions_id", "subscriptions", ["id"])
    op.create_index("ix_subscriptions_organization_id", "subscriptions", ["organization_id"])
    op.create_table("usage_records", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("organization_id", sa.String(), sa.ForeignKey("organizations.id")), sa.Column("username", sa.String(), nullable=False), sa.Column("provider", sa.String()), sa.Column("model", sa.String()), sa.Column("kind", sa.String(), nullable=False, server_default="chat"), sa.Column("tokens_in", sa.Integer()), sa.Column("tokens_out", sa.Integer()), sa.Column("duration_ms", sa.Integer()), sa.Column("created_at", sa.DateTime()))
    op.create_index("ix_usage_records_id", "usage_records", ["id"])
    op.create_index("ix_usage_records_organization_id", "usage_records", ["organization_id"])
    op.create_index("ix_usage_records_username", "usage_records", ["username"])
    op.create_index("ix_usage_records_created_at", "usage_records", ["created_at"])
    op.create_table("api_keys", sa.Column("id", sa.String(), primary_key=True), sa.Column("organization_id", sa.String(), sa.ForeignKey("organizations.id"), nullable=False), sa.Column("username", sa.String(), nullable=False), sa.Column("name", sa.String(), nullable=False), sa.Column("key_prefix", sa.String(), nullable=False), sa.Column("key_hash", sa.String(), nullable=False), sa.Column("revoked", sa.Integer(), nullable=False, server_default="0"), sa.Column("created_at", sa.DateTime()), sa.Column("last_used_at", sa.DateTime()))
    op.create_index("ix_api_keys_organization_id", "api_keys", ["organization_id"])
    op.create_index("ix_api_keys_username", "api_keys", ["username"])
    op.create_index("ix_api_keys_key_prefix", "api_keys", ["key_prefix"])
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"], unique=True)
    op.create_table("audit_logs", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("organization_id", sa.String(), sa.ForeignKey("organizations.id")), sa.Column("username", sa.String()), sa.Column("event", sa.String(), nullable=False), sa.Column("details", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime()))
    op.create_index("ix_audit_logs_id", "audit_logs", ["id"])
    op.create_index("ix_audit_logs_organization_id", "audit_logs", ["organization_id"])
    op.create_index("ix_audit_logs_username", "audit_logs", ["username"])
    op.create_index("ix_audit_logs_event", "audit_logs", ["event"])


def downgrade() -> None:
    for table in ["audit_logs", "api_keys", "usage_records", "subscriptions", "memberships", "memory_embeddings", "memories", "conversations", "chats", "organizations", "users"]:
        op.drop_table(table)
