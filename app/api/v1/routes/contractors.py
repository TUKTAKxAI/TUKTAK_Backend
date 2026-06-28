from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from datetime import datetime
from app.api.dependencies import get_current_contractor_id

from app.schemas.contractors import (
    ContractorMeResponse,
    ContractorProfileUpdateRequest,
    ContractorProfileUpdateResponse,
    ContractorServicesGetResponse,
    ContractorServicesPutRequest,
    ContractorServicesPutResponse,
    ContractorAlertUpdateRequest,
    ContractorAlertUpdateResponse,
    ContractorPublicProfileResponse
)
from app.services import contractors as contractor_service
from app.db.database import get_db


router = APIRouter(prefix="/contractors", tags=["Profile"])



# 시공자 본인 프로필 조회

@router.get("/me", response_model=ContractorMeResponse)
def get_my_profile(
    db: Session = Depends(get_db), 
    contractor_id: int = Depends(get_current_contractor_id)
):
    profile = contractor_service.get_my_profile(db, contractor_id)
    return {"success": True, "contractor": profile}



# 시공자 기본 정보 및 영업 상태 수정

@router.patch("/me", response_model=ContractorProfileUpdateResponse)
def update_my_profile(
    request: ContractorProfileUpdateRequest,
    db: Session = Depends(get_db),
    contractor_id: int = Depends(get_current_contractor_id)
):
    profile = contractor_service.update_my_profile(db, contractor_id, request)
    return {
        "success": True, 
        "contractor_id": profile.contractor_id,
        "approval_status": profile.approval_status,
        "available_status": profile.available_status,
        "updated_at": profile.updated_at
    }



# 내 전문 분야·서비스 지역 목록 조회

@router.get("/me/services", response_model=ContractorServicesGetResponse)
def get_my_services(
    db: Session = Depends(get_db),
    contractor_id: int = Depends(get_current_contractor_id)
):
    services = contractor_service.get_my_services(db, contractor_id)
    return {"success": True, "services": services}



# 전문 분야·서비스 가능 지역 일괄 저장

@router.put("/me/services", response_model=ContractorServicesPutResponse)
def bulk_update_my_services(
    request: ContractorServicesPutRequest,
    db: Session = Depends(get_db),
    contractor_id: int = Depends(get_current_contractor_id)
):
    new_services = contractor_service.bulk_update_my_services(db, contractor_id, request)
    return {
        "success": True, 
        "services": new_services, 
        "updated_at": datetime.now()
    }



# 신규 매칭 알림 수신 여부 설정

@router.patch("/me/alert-settings", response_model=ContractorAlertUpdateResponse)
def update_alert_settings(
    request: ContractorAlertUpdateRequest,
    db: Session = Depends(get_db),
    contractor_id: int = Depends(get_current_contractor_id)
):
    profile = contractor_service.update_alert_settings(db, contractor_id, request)
    return {
        "success": True,
        "contractor_id": profile.contractor_id,
        "matching_alert_enabled": profile.matching_alert_enabled,
        "updated_at": profile.updated_at
    }



# 사용자용 시공자 공개 프로필 및 평점 조회

@router.get("/{target_contractor_id}", response_model=ContractorPublicProfileResponse)
def get_public_profile(
    target_contractor_id: int, 
    db: Session = Depends(get_db)
):
    profile = contractor_service.get_public_profile(db, target_contractor_id)
    return {"success": True, "contractor": profile}