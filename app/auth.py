from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings


ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login"
)


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

try:
    from jose import JWTError, jwt  # type: ignore

    _JOSE = True

except Exception:  # pragma: no cover
    _JOSE = False

    class JWTError(Exception):
        pass

    class _JWT:
        @staticmethod
        def encode(
            payload: dict,
            key: str,
            algorithm: str = "HS256",
        ) -> str:

            header = {
                "alg": algorithm,
                "typ": "JWT",
            }

            def b64(obj: dict) -> str:
                return (
                    base64.urlsafe_b64encode(
                        json.dumps(
                            obj,
                            separators=(",", ":"),
                        ).encode()
                    )
                    .rstrip(b"=")
                    .decode()
                )

            header_b64 = b64(header)
            payload_b64 = b64(payload)

            signature = hmac.new(
                key.encode(),
                f"{header_b64}.{payload_b64}".encode(),
                hashlib.sha256,
            ).digest()

            signature_b64 = (
                base64.urlsafe_b64encode(signature)
                .rstrip(b"=")
                .decode()
            )

            return (
                f"{header_b64}."
                f"{payload_b64}."
                f"{signature_b64}"
            )

        @staticmethod
        def decode(
            token: str,
            key: str,
            algorithms: list[str] | None = None,
        ) -> dict:

            try:
                header_b64, payload_b64, signature_b64 = (
                    token.split(".")
                )

                raw_signature = hmac.new(
                    key.encode(),
                    f"{header_b64}.{payload_b64}".encode(),
                    hashlib.sha256,
                ).digest()

                expected_signature = (
                    base64.urlsafe_b64encode(
                        raw_signature
                    )
                    .rstrip(b"=")
                    .decode()
                )

                if not hmac.compare_digest(
                    signature_b64,
                    expected_signature,
                ):
                    raise JWTError(
                        "Invalid signature"
                    )

                padding = "=" * (
                    -len(payload_b64) % 4
                )

                payload = json.loads(
                    base64.urlsafe_b64decode(
                        (
                            payload_b64 + padding
                        ).encode()
                    )
                )

                if not isinstance(payload, dict):
                    raise JWTError(
                        "Invalid payload"
                    )

                return payload

            except JWTError:
                raise

            except Exception as exc:
                raise JWTError(
                    "Invalid token"
                ) from exc

    jwt = _JWT()


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

try:
    from passlib.context import CryptContext  # type: ignore

    # IMPORTANT:
    #
    # Existing Falcon users currently have bcrypt hashes:
    #
    #     $2b$12$...
    #
    # Therefore bcrypt MUST remain available for verification.
    #
    # New passwords use PBKDF2-SHA256.
    #
    pwd_context = CryptContext(
        schemes=[
            "pbkdf2_sha256",
            "bcrypt",
        ],
        deprecated=[
            "bcrypt",
        ],
    )

except Exception:  # pragma: no cover

    pwd_context = None


# ---------------------------------------------------------------------------
# Password fallback implementation
# ---------------------------------------------------------------------------

def _fallback_hash_password(
    password: str,
) -> str:

    salt = secrets.token_bytes(16)

    rounds = 200_000

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        rounds,
    )

    salt_b64 = (
        base64.urlsafe_b64encode(
            salt
        )
        .decode()
    )

    digest_b64 = (
        base64.urlsafe_b64encode(
            digest
        )
        .decode()
    )

    return (
        f"pbkdf2$"
        f"{rounds}$"
        f"{salt_b64}$"
        f"{digest_b64}"
    )


def _fallback_verify_password(
    password: str,
    encoded: str,
) -> bool:

    try:
        prefix, rounds, salt_b64, digest_b64 = (
            encoded.split("$")
        )

        if prefix != "pbkdf2":
            return False

        salt = base64.urlsafe_b64decode(
            salt_b64.encode()
        )

        expected_digest = (
            base64.urlsafe_b64decode(
                digest_b64.encode()
            )
        )

        actual_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt,
            int(rounds),
        )

        return hmac.compare_digest(
            actual_digest,
            expected_digest,
        )

    except Exception:
        return False


# ---------------------------------------------------------------------------
# Public password API
# ---------------------------------------------------------------------------

def hash_password(
    password: str,
) -> str:

    password = str(password)

    if pwd_context is not None:
        return pwd_context.hash(password)

    return _fallback_hash_password(
        password
    )


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:

    plain_password = str(
        plain_password
    )

    hashed_password = str(
        hashed_password
    )

    if not hashed_password:
        return False

    # Fallback hashes generated by Falcon's
    # portability implementation.
    if hashed_password.startswith(
        "pbkdf2$"
    ):
        return _fallback_verify_password(
            plain_password,
            hashed_password,
        )

    # Passlib handles:
    #
    #   $2b$...  bcrypt
    #   $pbkdf2-sha256$...  PBKDF2
    #
    # and other configured schemes.
    if pwd_context is None:
        return False

    try:
        return bool(
            pwd_context.verify(
                plain_password,
                hashed_password,
            )
        )

    except Exception:
        # Never allow a malformed or unsupported hash
        # to crash the authentication endpoint.
        return False


def needs_password_migration(
    hashed_password: str,
) -> bool:

    hashed_password = str(
        hashed_password
    )

    if not hashed_password:
        return True

    # Falcon's fallback format is already the current
    # portable format.
    if hashed_password.startswith(
        "pbkdf2$"
    ):
        return False

    # PBKDF2-SHA256 generated by Passlib is current.
    if hashed_password.startswith(
        "$pbkdf2-sha256$"
    ):
        return False

    # Existing bcrypt passwords are valid but deprecated.
    if hashed_password.startswith(
        "$2a$"
    ) or hashed_password.startswith(
        "$2b$"
    ) or hashed_password.startswith(
        "$2y$"
    ):
        return True

    # Unknown formats should be treated as requiring
    # migration rather than trusted as current.
    return True


# ---------------------------------------------------------------------------
# JWT access token
# ---------------------------------------------------------------------------

def create_access_token(
    data: dict[str, Any],
) -> str:

    to_encode = dict(data)

    expire = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    to_encode["exp"] = int(
        expire.timestamp()
    )

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )


# ---------------------------------------------------------------------------
# Authentication dependency
# ---------------------------------------------------------------------------

def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> str:

    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )

    try:

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        username = payload.get(
            "sub"
        )

        exp = payload.get(
            "exp"
        )

        if username is None:
            raise credentials_exception

        if exp is not None:

            if int(exp) < int(
                datetime.now(
                    timezone.utc
                ).timestamp()
            ):
                raise credentials_exception

        return str(username)

    except Exception:
        raise credentials_exception