import app.services.auth_service as auth_service
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from app.schemas import User

router = APIRouter()

users = {}

@router.post("/register")
def register(user: User):
    return auth_service.register(user)


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    return auth_service.login(form_data)


@router.get("/profile")
def profile(current_user: str = Depends(get_current_user)):
    return {
        "message": f"Welcome {current_user}!"
    }