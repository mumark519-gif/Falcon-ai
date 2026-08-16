from __future__ import annotations

from typing import Any, cast

from sqlalchemy.orm import Session

from app.auth import (
    create_access_token,
    hash_password,
    needs_password_migration,
    verify_password,
)
from app.models import User as UserModel


def register(
    user: Any,
    db: Session,
) -> dict[str, Any]:

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

    username = str(user.username)
    email = str(user.email)
    password = str(user.password)

    new_user = UserModel(
        username=username,
        email=email,
        password=hash_password(password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Every account starts with an isolated personal workspace.
    from app.enterprise.commercial import (
        ensure_personal_organization,
    )

    ensure_personal_organization(
        db,
        username,
    )

    return {
        "message": "User registered successfully"
    }


def login(
    form_data: Any,
    db: Session,
) -> dict[str, Any]:

    username = str(form_data.username)
    password = str(form_data.password)

    user = (
        db.query(UserModel)
        .filter(
            UserModel.username == username
        )
        .first()
    )

    if not user:
        return {
            "error": "Invalid username or password"
        }

    # SQLAlchemy's ORM type stubs can expose mapped columns as
    # Column[str] to static analyzers. At runtime this is the
    # actual database value, so explicitly convert it to str.
    stored_password = cast(
        str,
        user.password,
    )

    try:
        valid_password = verify_password(
            password,
            stored_password,
        )
    except Exception:
        # Never allow malformed/unsupported password hashes to
        # crash the login endpoint with HTTP 500.
        valid_password = False

    if not valid_password:
        return {
            "error": "Invalid username or password"
        }

    # Transparently upgrade an old password hash after successful
    # authentication. This is important because the existing
    # database contains bcrypt hashes while the new system uses
    # the configured current hashing scheme.
    try:
        if needs_password_migration(
            stored_password,
        ):
            user.password = cast(
                Any,
                hash_password(password),
            )

            db.add(user)
            db.commit()
            db.refresh(user)

    except Exception:
        # Authentication has already succeeded. Migration failure
        # should not prevent the user from logging in.
        db.rollback()

    token = create_access_token(
        {
            "sub": username
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }