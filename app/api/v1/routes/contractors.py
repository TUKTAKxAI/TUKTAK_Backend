from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_contractor_id
from app.db.database import get_db
from app.db.models import ContractorProfile, ContractorService
from app.schemas.contractors import (
    ContractorAlertUpdateRequest,
    ContractorAlertUpdateResponse,
    ContractorMeDetail,
    ContractorMeResponse,
    ContractorProfileUpdateRequest,
    ContractorProfileUpdateResponse,
    ContractorPublicProfileDetail,
    ContractorPublicProfileResponse,
    ContractorServiceDetail,
    ContractorServicePutResultItem,
    ContractorServicesGetResponse,
    ContractorServicesPutRequest,
    ContractorServicesPutResponse,
)

router = APIRouter(prefix="/contractors", tags=["Profile"])


async def _get_profile(db: AsyncSession, contractor_id: int) -> ContractorProfile:
    result = await db.execute(
        select(ContractorProfile).where(ContractorProfile.contractor_id == contractor_id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="Contractor profile not found")
    return profile


@router.get("/me", response_model=ContractorMeResponse)
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    contractor_id: int = Depends(get_current_contractor_id),
) -> ContractorMeResponse:
    return ContractorMeResponse(contractor=ContractorMeDetail.model_validate(await _get_profile(db, contractor_id)))


@router.patch("/me", response_model=ContractorProfileUpdateResponse)
async def update_my_profile(
    payload: ContractorProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    contractor_id: int = Depends(get_current_contractor_id),
) -> ContractorProfileUpdateResponse:
    profile = await _get_profile(db, contractor_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    await db.commit()
    await db.refresh(profile)
    return ContractorProfileUpdateResponse(
        contractor_id=profile.contractor_id,
        approval_status=profile.approval_status,
        available_status=profile.available_status,
        updated_at=profile.updated_at,
    )


@router.get("/me/services", response_model=ContractorServicesGetResponse)
async def get_my_services(
    db: AsyncSession = Depends(get_db),
    contractor_id: int = Depends(get_current_contractor_id),
) -> ContractorServicesGetResponse:
    result = await db.execute(
        select(ContractorService).where(ContractorService.contractor_id == contractor_id)
    )
    return ContractorServicesGetResponse(
        services=[ContractorServiceDetail.model_validate(item) for item in result.scalars()]
    )


@router.put("/me/services", response_model=ContractorServicesPutResponse)
async def bulk_update_my_services(
    payload: ContractorServicesPutRequest,
    db: AsyncSession = Depends(get_db),
    contractor_id: int = Depends(get_current_contractor_id),
) -> ContractorServicesPutResponse:
    await db.execute(delete(ContractorService).where(ContractorService.contractor_id == contractor_id))
    services = [
        ContractorService(contractor_id=contractor_id, **item.model_dump())
        for item in payload.services
    ]
    db.add_all(services)
    await db.commit()
    for service in services:
        await db.refresh(service)
    return ContractorServicesPutResponse(
        services=[ContractorServicePutResultItem.model_validate(s) for s in services],
        updated_at=datetime.now(),
    )


@router.patch("/me/alert-settings", response_model=ContractorAlertUpdateResponse)
async def update_alert_settings(
    payload: ContractorAlertUpdateRequest,
    db: AsyncSession = Depends(get_db),
    contractor_id: int = Depends(get_current_contractor_id),
) -> ContractorAlertUpdateResponse:
    profile = await _get_profile(db, contractor_id)
    profile.matching_alert_enabled = payload.matching_alert_enabled
    await db.commit()
    await db.refresh(profile)
    return ContractorAlertUpdateResponse(
        contractor_id=profile.contractor_id,
        matching_alert_enabled=profile.matching_alert_enabled,
        updated_at=profile.updated_at,
    )


@router.get("/{contractor_id}", response_model=ContractorPublicProfileResponse)
async def get_public_profile(
    contractor_id: int,
    db: AsyncSession = Depends(get_db),
) -> ContractorPublicProfileResponse:
    profile = await _get_profile(db, contractor_id)
    result = await db.execute(
        select(ContractorService).where(
            ContractorService.contractor_id == contractor_id,
            ContractorService.is_active.is_(True),
        )
    )
    data = ContractorPublicProfileDetail(
        contractor_id=profile.contractor_id,
        business_name=profile.business_name,
        introduction=profile.introduction,
        rating_avg=profile.rating_avg,
        review_count=profile.review_count,
        available_status=profile.available_status,
        services=[ContractorServiceDetail.model_validate(item) for item in result.scalars()],
    )
    return ContractorPublicProfileResponse(contractor=data)
