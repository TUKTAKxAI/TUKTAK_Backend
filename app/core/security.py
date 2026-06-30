import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt
from passlib.context import CryptContext

from app.core.settings import settings

TokenType = Literal["access", "refresh"]
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def _create_token(
    user_id: int,
    user_type: str,
    token_type: TokenType,
    expires_in: int,
) -> tuple[str, datetime, str]:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=expires_in)
    jti = str(uuid.uuid4())
    payload = {
        "sub": str(user_id),
        "user_type": user_type,
        "type": token_type,
        "jti": jti,
        "iat": now,
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_at, jti


def create_access_token(user_id: int, user_type: str) -> tuple[str, datetime, str]:
    return _create_token(
        user_id,
        user_type,
        "access",
        settings.access_token_expire_seconds,
    )


def create_refresh_token(user_id: int, user_type: str) -> tuple[str, datetime, str]:
    return _create_token(
        user_id,
        user_type,
        "refresh",
        settings.refresh_token_expire_seconds,
    )


def decode_token(token: str, expected_type: TokenType | None = None) -> dict:
    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.jwt_algorithm],
        options={"require": ["sub", "type", "jti", "iat", "exp"]},
    )
    if expected_type is not None and payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("Unexpected token type")
    return payload


def hash_refresh_token(token: str) -> str:
    material = f"{settings.token_pepper}:{token}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()
