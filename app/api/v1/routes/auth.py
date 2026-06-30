from fastapi import APIRouter, Depends, Query, Request
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
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
        user_type="CUSTOMER",
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
        user_type="CONTRACTOR",
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
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    result = await auth_service.login(db, payload)
    user = result.pop("user")
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
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> RefreshResponse:
    return RefreshResponse(**(await auth_service.refresh(db, payload.refresh_token)))


@router.post("/logout", response_model=MessageResponse)
async def logout(
    payload: LogoutRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await auth_service.logout(db, payload.refresh_token)
    return MessageResponse(message="Logged out")
