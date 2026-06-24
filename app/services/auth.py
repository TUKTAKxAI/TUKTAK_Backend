from datetime import datetime, timezone

import jwt
from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.agreements import AgreementDefinition, get_agreement_catalog
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.core.settings import settings
from app.db.models import AuthToken, ContractorProfile, User, UserAgreement
from app.schemas.auth import (
    AgreementInput,
    ContractorSignupRequest,
    CustomerSignupRequest,
    LoginRequest,
)


def _unauthorized(detail: str = "Invalid credentials") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def is_email_available(db: AsyncSession, email: str) -> bool:
    result = await db.execute(select(User.user_id).where(User.email == str(email)))
    return result.scalar_one_or_none() is None


def _validate_agreements(
    agreements: list[AgreementInput],
) -> list[tuple[AgreementInput, AgreementDefinition]]:
    catalog = {item.terms_type: item for item in get_agreement_catalog()}
    submitted: dict[str, AgreementInput] = {}
    for agreement in agreements:
        if agreement.terms_type in submitted:
            raise HTTPException(status_code=422, detail="Duplicate agreement type")
        definition = catalog.get(agreement.terms_type)
        if definition is None or definition.terms_version != agreement.terms_version:
            raise HTTPException(status_code=422, detail="Unknown or outdated agreement")
        submitted[agreement.terms_type] = agreement

    missing = [
        item.terms_type
        for item in catalog.values()
        if item.is_required
        and (item.terms_type not in submitted or not submitted[item.terms_type].is_agreed)
    ]
    if missing:
        raise HTTPException(
            status_code=422,
            detail={"code": "REQUIRED_AGREEMENT_MISSING", "terms_types": missing},
        )
    return [(agreement, catalog[agreement.terms_type]) for agreement in agreements]


async def _create_user(
    db: AsyncSession,
    payload: CustomerSignupRequest | ContractorSignupRequest,
    user_type: str,
    ip_address: str | None,
) -> User:
    agreement_pairs = _validate_agreements(payload.agreements)
    normalized_email = str(payload.email).strip().lower()
    now = datetime.now(timezone.utc)
    user = User(
        login_id=normalized_email,
        email=normalized_email,
        password_hash=hash_password(payload.password),
        nickname=payload.nickname,
        name=payload.name,
        phone=payload.phone,
        user_type=user_type,
        account_status="ACTIVE",
    )
    db.add(user)
    await db.flush()

    db.add_all(
        [
            UserAgreement(
                user_id=user.user_id,
                terms_type=agreement.terms_type,
                terms_version=agreement.terms_version,
                terms_title=definition.terms_title,
                terms_content_url=definition.terms_content_url,
                is_required=definition.is_required,
                is_agreed=agreement.is_agreed,
                agreed_at=now,
                ip_address=ip_address,
            )
            for agreement, definition in agreement_pairs
        ]
    )
    return user


async def signup_customer(
    db: AsyncSession,
    payload: CustomerSignupRequest,
    ip_address: str | None,
) -> User:
    try:
        async with db.begin():
            user = await _create_user(db, payload, "CUSTOMER", ip_address)
        await db.refresh(user)
        return user
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email, nickname, or phone already exists") from exc


async def signup_contractor(
    db: AsyncSession,
    payload: ContractorSignupRequest,
    ip_address: str | None,
) -> tuple[User, ContractorProfile]:
    try:
        async with db.begin():
            user = await _create_user(db, payload, "CONTRACTOR", ip_address)
            profile = ContractorProfile(
                contractor_id=user.user_id,
                business_name=payload.business_name,
                representative_name=payload.representative_name,
                business_number=payload.business_number,
                contact_phone=payload.contact_phone,
                business_status=payload.business_status,
                approval_status="PENDING",
            )
            db.add(profile)
        await db.refresh(user)
        await db.refresh(profile)
        return user, profile
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email, nickname, phone, or business number already exists",
        ) from exc


async def _persist_refresh_token(
    db: AsyncSession,
    user_id: int,
    refresh_token: str,
    expires_at: datetime,
) -> None:
    db.add(
        AuthToken(
            user_id=user_id,
            token_type="REFRESH_TOKEN",
            token_hash=hash_refresh_token(refresh_token),
            expires_at=expires_at,
        )
    )


async def login(db: AsyncSession, payload: LoginRequest) -> dict:
    email = str(payload.email).strip().lower()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if (
        user is None
        or user.password_hash is None
        or not verify_password(payload.password, user.password_hash)
    ):
        raise _unauthorized("Invalid email or password")
    if user.account_status != "ACTIVE":
        raise HTTPException(status_code=403, detail="Account is not active")

    access_token, _, _ = create_access_token(user.user_id, user.user_type)
    refresh_token, refresh_expires_at, _ = create_refresh_token(user.user_id, user.user_type)
    user.last_login_at = datetime.now(timezone.utc)
    await _persist_refresh_token(db, user.user_id, refresh_token, refresh_expires_at)
    await db.commit()
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": settings.access_token_expire_seconds,
        "user": user,
    }


async def refresh(db: AsyncSession, refresh_token: str) -> dict:
    try:
        payload = decode_token(refresh_token, "refresh")
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError, KeyError) as exc:
        raise _unauthorized("Invalid refresh token") from exc

    now = datetime.now(timezone.utc)
    token_hash = hash_refresh_token(refresh_token)
    result = await db.execute(
        select(AuthToken, User)
        .join(User, User.user_id == AuthToken.user_id)
        .where(
            AuthToken.user_id == user_id,
            AuthToken.token_type == "REFRESH_TOKEN",
            AuthToken.token_hash == token_hash,
            AuthToken.used_at.is_(None),
            AuthToken.revoked_at.is_(None),
            AuthToken.expires_at > now,
            User.account_status == "ACTIVE",
        )
        .with_for_update()
    )
    row = result.one_or_none()
    if row is None:
        raise _unauthorized("Refresh token is expired, revoked, or already used")
    stored_token, user = row
    stored_token.used_at = now
    stored_token.revoked_at = now

    access_token, _, _ = create_access_token(user.user_id, user.user_type)
    new_refresh_token, refresh_expires_at, _ = create_refresh_token(
        user.user_id, user.user_type
    )
    await _persist_refresh_token(db, user.user_id, new_refresh_token, refresh_expires_at)
    await db.commit()
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "expires_in": settings.access_token_expire_seconds,
    }


async def logout(db: AsyncSession, refresh_token: str) -> None:
    now = datetime.now(timezone.utc)
    await db.execute(
        update(AuthToken)
        .where(
            AuthToken.token_hash == hash_refresh_token(refresh_token),
            AuthToken.token_type == "REFRESH_TOKEN",
            AuthToken.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    await db.commit()
