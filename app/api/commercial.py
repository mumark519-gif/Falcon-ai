from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.enterprise.commercial import PLANS, create_api_key, ensure_personal_organization, get_membership, monthly_usage
from app.models import ApiKey, Membership, Organization, Subscription

router = APIRouter(prefix="/commercial", tags=["commercial"])


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class MemberAdd(BaseModel):
    username: str = Field(min_length=1)
    role: str = Field(default="user", pattern="^(admin|developer|analyst|user)$")


class ApiKeyCreate(BaseModel):
    name: str = Field(default="API key", min_length=1, max_length=80)


def _membership_or_403(db: Session, username: str, organization_id: str):
    membership = get_membership(db, username, organization_id)
    if not membership:
        raise HTTPException(status_code=403, detail="You are not a member of this organization.")
    return membership


@router.get("/plans")
def plans():
    return {"plans": PLANS}


@router.get("/organization")
def organization(current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    org = ensure_personal_organization(db, current_user)
    members = db.query(Membership).filter(Membership.organization_id == org.id).all()
    return {"id": org.id, "name": org.name, "owner_username": org.owner_username, "plan": org.plan, "members": [{"username": m.username, "role": m.role} for m in members]}


@router.post("/organization")
def create_organization(body: OrganizationCreate, current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    org = Organization(id=__import__("uuid").uuid4().hex, name=body.name, owner_username=current_user, plan="free")
    db.add(org)
    db.flush()
    db.add(Membership(organization_id=org.id, username=current_user, role="admin"))
    db.add(Subscription(organization_id=org.id, plan="free", status="active"))
    db.commit()
    return {"id": org.id, "name": org.name, "plan": org.plan}


@router.post("/organization/{organization_id}/members")
def add_member(organization_id: str, body: MemberAdd, current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    actor = _membership_or_403(db, current_user, organization_id)
    if actor.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator permission required.")
    if not db.query(__import__("app.models", fromlist=["User"]).User).filter_by(username=body.username).first():
        raise HTTPException(status_code=404, detail="User not found.")
    existing = get_membership(db, body.username, organization_id)
    if existing:
        existing.role = body.role
    else:
        db.add(Membership(organization_id=organization_id, username=body.username, role=body.role))
    db.commit()
    return {"organization_id": organization_id, "username": body.username, "role": body.role}


@router.get("/usage")
def usage(current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    org = ensure_personal_organization(db, current_user)
    plan = PLANS.get(org.plan, PLANS["free"])
    used = monthly_usage(db, org.id)
    return {"organization_id": org.id, "plan": org.plan, "used": used, "limit": plan["monthly_requests"], "remaining": max(plan["monthly_requests"] - used, 0)}


@router.get("/subscription")
def subscription(current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    org = ensure_personal_organization(db, current_user)
    sub = db.query(Subscription).filter(Subscription.organization_id == org.id).order_by(Subscription.id.desc()).first()
    return {"organization_id": org.id, "plan": sub.plan if sub else org.plan, "status": sub.status if sub else "active", "provider_customer_id": sub.provider_customer_id if sub else None}


@router.post("/api-keys")
def create_key(body: ApiKeyCreate, current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    record, raw = create_api_key(db, current_user, body.name)
    return {"id": record.id, "name": record.name, "prefix": record.key_prefix, "api_key": raw, "warning": "Store this key now; Falcon never stores the plaintext key."}


@router.get("/api-keys")
def list_keys(current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(ApiKey).filter(ApiKey.username == current_user).order_by(ApiKey.created_at.desc()).all()
    return [{"id": row.id, "name": row.name, "prefix": row.key_prefix, "revoked": bool(row.revoked), "created_at": row.created_at} for row in rows]


@router.delete("/api-keys/{key_id}")
def revoke_key(key_id: str, current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.query(ApiKey).filter(ApiKey.id == key_id, ApiKey.username == current_user).first()
    if not row:
        raise HTTPException(status_code=404, detail="API key not found.")
    row.revoked = 1
    db.commit()
    return {"message": "API key revoked."}
