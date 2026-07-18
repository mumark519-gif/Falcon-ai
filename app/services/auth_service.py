from fastapi import HTTPException

from app.auth import (
    create_access_token,
    hash_password,
    verify_password,
)

from app.database import SessionLocal
from app.models import User as UserModel


def register(user):

    db = SessionLocal()

    try:
        existing_user = (
            db.query(UserModel)
            .filter(
                UserModel.username == user.username
            )
            .first()
        )

        if existing_user:
            return {
                "error": "User already exists"
            }

        new_user = UserModel(
            username=user.username,
            password=hash_password(user.password),
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "message": "User registered successfully"
        }

    finally:
        db.close()


def login(form_data):

    db = SessionLocal()

    try:
        user = (
            db.query(UserModel)
            .filter(
                UserModel.username == form_data.username
            )
            .first()
        )

        if not user:
            return {
                "error": "Invalid username or password"
            }

        if not verify_password(
            form_data.password,
            user.password,
        ):
            return {
                "error": "Invalid username or password"
            }

        token = create_access_token(
            {
                "sub": user.username
            }
        )

        return {
            "access_token": token,
            "token_type": "bearer"
        }

    finally:
        db.close()