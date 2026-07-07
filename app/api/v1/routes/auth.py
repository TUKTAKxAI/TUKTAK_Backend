from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.core.settings import settings
from app.schemas.auth import (
    AuthUser,
    AvailabilityResponse,
    ContractorSignupRequest,
    CustomerSignupRequest,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RefreshResponse,
    SignupResponse,
)
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup/customer", response_model=SignupResponse, status_code=201)
async def signup_customer(
    payload: CustomerSignupRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> SignupResponse:
    user = await auth_service.signup_customer(
        db, payload, request.client.host if request.client else None
    )
    return SignupResponse(
        user_id=user.user_id,
        user_type=user.user_type,
        created_at=user.created_at,
    )


@router.post("/signup/contractor", response_model=SignupResponse, status_code=201)
async def signup_contractor(
    payload: ContractorSignupRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> SignupResponse:
    user, profile = await auth_service.signup_contractor(
        db, payload, request.client.host if request.client else None
    )
    return SignupResponse(
        user_id=user.user_id,
        contractor_id=profile.contractor_id,
        user_type=user.user_type,
        approval_status=profile.approval_status,
        created_at=user.created_at,
    )


@router.get("/email-availability", response_model=AvailabilityResponse)
async def email_availability(
    email: EmailStr = Query(...),
    db: AsyncSession = Depends(get_db),
) -> AvailabilityResponse:
    return AvailabilityResponse(available=await auth_service.is_email_available(db, str(email)))


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    result = await auth_service.login(db, payload)
    user = result.pop("user")
    request.state.auth_tokens = {
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
    }
    return LoginResponse(
        **result,
        user=AuthUser(
            user_id=user.user_id,
            nickname=user.nickname,
            user_type=user.user_type,
        ),
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(
    request: Request,
    payload: RefreshRequest | None = Body(None),
    db: AsyncSession = Depends(get_db),
) -> RefreshResponse:
    refresh_token = (
        payload.refresh_token
        if payload is not None
        else request.cookies.get(settings.auth_refresh_cookie_name)
    )
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is required",
        )
    result = await auth_service.refresh(db, refresh_token)
    request.state.auth_tokens = {
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
    }
    return RefreshResponse(**result)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    payload: LogoutRequest | None = Body(None),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    refresh_token = (
        payload.refresh_token
        if payload is not None
        else request.cookies.get(settings.auth_refresh_cookie_name)
    )
    if refresh_token is not None:
        await auth_service.logout(db, refresh_token)
    request.state.clear_auth_cookies = True
    return MessageResponse(message="Logged out")
