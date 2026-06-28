from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.common import UserMe, UserMeResponse, UserUpdateResponse

router = APIRouter(prefix="/users", tags=["User"])


@router.get("/me", response_model=UserMeResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserMeResponse:
    return UserMeResponse(user=UserMe.model_validate(current_user))


@router.patch("/me", response_model=UserUpdateResponse)
async def update_me(
    nickname: str | None = Form(None),
    name: str | None = Form(None),
    phone: str | None = Form(None),
    profile_image: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserUpdateResponse:
    if nickname is not None:
        current_user.nickname = nickname
    if name is not None:
        current_user.name = name
    if phone is not None:
        current_user.phone = phone
    if profile_image is not None:
        current_user.profile_image_url = f"/uploads/profile/{current_user.user_id}/{profile_image.filename}"
    await db.commit()
    await db.refresh(current_user)
    return UserUpdateResponse(
        user={
            "nickname": current_user.nickname,
            "name": current_user.name,
            "phone": current_user.phone,
            "profile_image_url": current_user.profile_image_url,
            "updated_at": current_user.updated_at or datetime.now(),
        }
    )
