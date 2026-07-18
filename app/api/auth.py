from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import auth, schemas
from app.database import get_db
from app.services import auth_service


router = APIRouter()


@router.post("/register")
def register(
    user: schemas.User,
    db: Session = Depends(get_db),
):
    return auth_service.register(user, db)


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    return auth_service.login(form_data, db)


@router.get("/profile")
def profile(
    current_user: str = Depends(auth.get_current_user),
):
    return {
        "message": f"Welcome {current_user}!"
    }