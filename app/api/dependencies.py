import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.database import get_db
from app.db.models import User

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials, "access")
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError, KeyError) as exc:
        raise unauthorized from exc

    result = await db.execute(
        select(User).where(User.user_id == user_id, User.account_status == "ACTIVE")
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise unauthorized
    return user


def require_roles(*roles: str):
    async def dependency(user: User = Depends(get_current_user)) -> User:
        has_role = user.user_type in roles or (
            user.user_type == "BOTH" and any(role in {"CUSTOMER", "CONTRACTOR"} for role in roles)
        )
        if not has_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return dependency


async def get_current_contractor_id(
    user: User = Depends(require_roles("CONTRACTOR")),
) -> int:
    return user.user_id
