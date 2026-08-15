from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings

ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

try:
    from jose import JWTError, jwt  # type: ignore
    _JOSE = True
except Exception:  # pragma: no cover - portability fallback
    _JOSE = False
    class JWTError(Exception):
        pass

    class _JWT:
        @staticmethod
        def encode(payload: dict, key: str, algorithm: str = "HS256") -> str:
            header = {"alg": algorithm, "typ": "JWT"}
            def b64(obj):
                return base64.urlsafe_b64encode(
                    json.dumps(obj, separators=(",", ":")).encode()
                ).rstrip(b"=").decode()
            h, p = b64(header), b64(payload)
            sig = hmac.new(key.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
            return f"{h}.{p}." + base64.urlsafe_b64encode(sig).rstrip(b"=").decode()

        @staticmethod
        def decode(token: str, key: str, algorithms=None) -> dict:
            try:
                h, p, s = token.split(".")
                raw = hmac.new(key.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
                expected = base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
                if not hmac.compare_digest(s, expected):
                    raise JWTError("Invalid signature")
                pad = "=" * (-len(p) % 4)
                return json.loads(base64.urlsafe_b64decode((p + pad).encode()))
            except Exception as exc:
                if isinstance(exc, JWTError):
                    raise
                raise JWTError("Invalid token") from exc
    jwt = _JWT()

try:
    from passlib.context import CryptContext  # type: ignore
    # Try to create context with only PBKDF2 to avoid bcrypt issues
    try:
        pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
    except Exception:
        # Fallback: try with argon2
        pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
except Exception:  # pragma: no cover - portability fallback
    class _PasswordContext:
        def hash(self, password: str) -> str:
            salt = secrets.token_bytes(16)
            digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
            return "pbkdf2$200000$" + base64.urlsafe_b64encode(salt).decode() + "$" + base64.urlsafe_b64encode(digest).decode()
        def verify(self, password: str, encoded: str) -> bool:
            try:
                _, rounds, salt_b64, digest_b64 = encoded.split("$")
                salt = base64.urlsafe_b64decode(salt_b64.encode())
                digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(rounds))
                return hmac.compare_digest(
                    digest,
                    base64.urlsafe_b64decode(digest_b64.encode()),
                )
            except Exception:
                return False
    pwd_context = _PasswordContext()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = dict(data)
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode["exp"] = int(expire.timestamp())
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        exp = payload.get("exp")
        if username is None:
            raise credentials_exception
        if exp is not None and int(exp) < int(datetime.now(timezone.utc).timestamp()):
            raise credentials_exception
        return str(username)
    except Exception:
        raise credentials_exception
