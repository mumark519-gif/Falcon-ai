from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app import schemas
from app import auth
from app.services import auth_service


router = APIRouter()


@router.post("/register")
def register(user: schemas.User):
    return auth_service.register(user)


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    return auth_service.login(form_data)


@router.get("/profile")
def profile(
    current_user: str = Depends(auth.get_current_user),
):
    return {
        "message": f"Welcome {current_user}!"
    }