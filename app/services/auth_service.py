from sqlalchemy.orm import Session

from app.auth import (
    create_access_token,
    hash_password,
    verify_password,
)

from app.models import User as UserModel


def register(
    user,
    db: Session,
):

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
        email=user.email,
        password=hash_password(user.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Every account starts with an isolated personal workspace. Commercial
    # organizations can be created later without changing the auth contract.
    from app.enterprise.commercial import ensure_personal_organization
    ensure_personal_organization(db, new_user.username)

    return {
        "message": "User registered successfully"
    }


def login(
    form_data,
    db: Session,
):

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