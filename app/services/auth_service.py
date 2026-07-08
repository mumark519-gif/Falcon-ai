from app.database import SessionLocal
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
)

users = {}

def register(user):

    if user.username in users:
        return {
            "error": "User already exists"
        }

    users[user.username] = hash_password(user.password)

    return {
        "message": "User registered successfully"
    }

def login(form_data):

    if form_data.username not in users:
        return {
            "error": "Invalid username or password"
        }

    if not verify_password(
        form_data.password,
        users[form_data.username]
    ):
        return {
            "error": "Invalid username or password"
        }

    token = create_access_token(
        {"sub": form_data.username}
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }