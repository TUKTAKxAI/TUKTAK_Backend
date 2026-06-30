from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
from typing import List

from app.db.models.contractor_profile import ContractorProfile
from app.db.models.contractor_service import ContractorService
from app.schemas.contractors import (
    ContractorProfileUpdateRequest,
    ContractorServicesPutRequest,
    ContractorAlertUpdateRequest
)

def get_my_profile(db: Session, contractor_id: int) -> ContractorProfile:
    profile = db.query(ContractorProfile).filter(
        ContractorProfile.contractor_id == contractor_id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="시공자 프로필을 찾을 수 없습니다."
        )
    return profile


def update_my_profile(
    db: Session, 
    contractor_id: int, 
    request_data: ContractorProfileUpdateRequest
) -> ContractorProfile:
    profile = db.query(ContractorProfile).filter(
        ContractorProfile.contractor_id == contractor_id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="시공자 프로필을 찾을 수 없습니다."
        )

    update_data = request_data.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(profile, key, value)
        
    db.commit()
    db.refresh(profile)
    return profile


def get_my_services(db: Session, contractor_id: int) -> List[ContractorService]:
    services = db.query(ContractorService).filter(
        ContractorService.contractor_id == contractor_id
    ).all()
    return services


def bulk_update_my_services(
    db: Session, 
    contractor_id: int, 
    request_data: ContractorServicesPutRequest
) -> List[ContractorService]:
    db.query(ContractorService).filter(
        ContractorService.contractor_id == contractor_id
    ).delete()
    
    new_services = []
    for item in request_data.services:
        new_service = ContractorService(
            contractor_id=contractor_id,
            **item.model_dump()
        )
        new_services.append(new_service)
        
    db.add_all(new_services)
    db.commit()
    
    for service in new_services:
        db.refresh(service)
        
    return new_services


def update_alert_settings(
    db: Session, 
    contractor_id: int, 
    request_data: ContractorAlertUpdateRequest
) -> ContractorProfile:
    profile = db.query(ContractorProfile).filter(
        ContractorProfile.contractor_id == contractor_id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="시공자 프로필을 찾을 수 없습니다."
        )
        
    profile.matching_alert_enabled = request_data.matching_alert_enabled
    db.commit()
    db.refresh(profile)
    return profile


def get_public_profile(db: Session, target_contractor_id: int) -> ContractorProfile:
    profile = db.query(ContractorProfile).filter(
        ContractorProfile.contractor_id == target_contractor_id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="해당 시공자를 찾을 수 없습니다."
        )
    return profile