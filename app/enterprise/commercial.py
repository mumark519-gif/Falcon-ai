from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import ApiKey, AuditLogRecord, Membership, Organization, Subscription, UsageRecord, User

PLANS = {
    "free": {"monthly_price": 0, "monthly_requests": 100, "members": 1},
    "pro": {"monthly_price": 20, "monthly_requests": 5000, "members": 5},
    "business": {"monthly_price": 99, "monthly_requests": 50000, "members": 50},
    "enterprise": {"monthly_price": 0, "monthly_requests": 1000000, "members": 1000},
}


def now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_personal_organization(db: Session, username: str) -> Organization:
    membership = db.query(Membership).filter(Membership.username == username).first()
    if membership:
        org = db.query(Organization).filter(Organization.id == membership.organization_id).first()
        if org:
            return org

    org = Organization(id=str(uuid4()), name=f"{username}'s workspace", owner_username=username, plan="free")
    db.add(org)
    db.flush()
    db.add(Membership(organization_id=org.id, username=username, role="admin"))
    db.add(Subscription(organization_id=org.id, plan="free", status="active"))
    db.commit()
    db.refresh(org)
    return org


def get_membership(db: Session, username: str, organization_id: str | None = None) -> Membership | None:
    query = db.query(Membership).filter(Membership.username == username)
    if organization_id:
        query = query.filter(Membership.organization_id == organization_id)
    return query.first()


def record_usage(
    db: Session,
    *,
    username: str,
    provider: str | None,
    model: str | None,
    kind: str = "chat",
    duration_ms: float | None = None,
    tokens_in: int | None = None,
    tokens_out: int | None = None,
) -> UsageRecord:
    membership = get_membership(db, username)
    record = UsageRecord(
        organization_id=membership.organization_id if membership else None,
        username=username,
        provider=provider,
        model=model,
        kind=kind,
        duration_ms=duration_ms,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        created_at=now(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def monthly_usage(db: Session, organization_id: str) -> int:
    start = now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return (
        db.query(UsageRecord)
        .filter(UsageRecord.organization_id == organization_id, UsageRecord.created_at >= start)
        .count()
    )


def enforce_plan_limit(db: Session, username: str) -> None:
    membership = get_membership(db, username)
    if not membership:
        return
    org = db.query(Organization).filter(Organization.id == membership.organization_id).first()
    if not org:
        return
    limit = PLANS.get(org.plan, PLANS["free"])["monthly_requests"]
    if monthly_usage(db, org.id) >= limit:
        raise PermissionError(f"Monthly request limit reached for the {org.plan} plan.")


def create_api_key(db: Session, username: str, name: str) -> tuple[ApiKey, str]:
    membership = get_membership(db, username)
    if not membership:
        membership = get_membership(db, username) or Membership(organization_id=ensure_personal_organization(db, username).id, username=username, role="admin")
    raw = "falcon_" + secrets.token_urlsafe(32)
    record = ApiKey(
        id=str(uuid4()),
        organization_id=membership.organization_id,
        username=username,
        name=name.strip() or "API key",
        key_prefix=raw[:14],
        key_hash=hashlib.sha256(raw.encode()).hexdigest(),
        revoked=False,
        created_at=now(),
    )
    db.add(record)
    db.add(AuditLogRecord(username=username, organization_id=membership.organization_id, event="api_key_created", details={"name": record.name}, created_at=now()))
    db.commit()
    db.refresh(record)
    return record, raw
