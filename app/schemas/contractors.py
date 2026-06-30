from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum



# 공통 Enum (상태값 및 결과값 정의)

class BusinessStatus(str, Enum):
    INDIVIDUAL = "INDIVIDUAL"
    BUSINESS = "BUSINESS"
    CORPORATE = "CORPORATE"

class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"

class AvailableStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    OFFLINE = "OFFLINE"

class MatchStatus(str, Enum):
    PENDING = "PENDING"
    SELECTED = "SELECTED"
    OTHER_SELECTED = "OTHER_SELECTED"
    CANCELED = "CANCELED"



# 시공자 본인 프로필 조회

class ContractorMeDetail(BaseModel):
    contractor_id: int
    business_name: str = Field(..., max_length=100)
    representative_name: str = Field(..., max_length=50)
    contact_phone: str = Field(..., max_length=20)
    business_number: Optional[str] = Field(None, max_length=20)
    introduction: Optional[str] = None
    business_status: BusinessStatus 
    approval_status: ApprovalStatus
    document_status_json: Optional[Dict[str, Any]] = None 
    service_radius_km: Optional[Decimal] = None 
    rating_avg: Decimal
    review_count: int
    matching_alert_enabled: bool
    available_status: AvailableStatus 
    created_at: datetime 
    updated_at: datetime 

    model_config = ConfigDict(from_attributes=True)

class ContractorMeResponse(BaseModel):
    success: bool = True
    contractor: ContractorMeDetail



# 시공자 기본 정보 및 영업 상태 수정

class ContractorProfileUpdateRequest(BaseModel):
    business_name: Optional[str] = Field(None, max_length=100)
    representative_name: Optional[str] = Field(None, max_length=50)
    contact_phone: Optional[str] = Field(None, max_length=20)
    introduction: Optional[str] = None
    business_status: Optional[BusinessStatus] = None
    service_radius_km: Optional[Decimal] = None
    available_status: Optional[AvailableStatus] = None

class ContractorProfileUpdateResponse(BaseModel):
    success: bool = True
    contractor_id: int
    approval_status: ApprovalStatus
    available_status: AvailableStatus
    updated_at: datetime



# 내 전문 분야·서비스 지역 목록 조회

class ContractorServiceDetail(BaseModel):
    contractor_service_id: int
    service_task_id: int
    region_code_id: int
    experience_years: Optional[int] = None
    minimum_visit_fee: Optional[Decimal] = None
    service_radius_km: Optional[Decimal] = None
    is_active: bool
    updated_at: datetime 

    model_config = ConfigDict(from_attributes=True)

class ContractorServicesGetResponse(BaseModel):
    success: bool = True
    services: List[ContractorServiceDetail]



# 전문 분야·서비스 가능 지역 일괄 저장

class ContractorServicePutItem(BaseModel):
    service_task_id: int
    region_code_id: int
    experience_years: Optional[int] = None
    minimum_visit_fee: Optional[Decimal] = None
    service_radius_km: Optional[Decimal] = None
    is_active: bool

class ContractorServicesPutRequest(BaseModel):
    services: List[ContractorServicePutItem]

class ContractorServicePutResultItem(BaseModel):
    contractor_service_id: int
    service_task_id: int
    region_code_id: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class ContractorServicesPutResponse(BaseModel):
    success: bool = True
    services: List[ContractorServicePutResultItem]
    updated_at: datetime



# 5. 신규 매칭 알림 수신 여부 설정

class ContractorAlertUpdateRequest(BaseModel):
    matching_alert_enabled: bool

class ContractorAlertUpdateResponse(BaseModel):
    success: bool = True
    contractor_id: int
    matching_alert_enabled: bool
    updated_at: datetime



# 6. 사용자용 시공자 공개 프로필 및 평점 조회

class ContractorPublicProfileDetail(BaseModel):
    contractor_id: int
    business_name: str = Field(..., max_length=100)
    introduction: Optional[str] = None
    rating_avg: Decimal
    review_count: int
    available_status: AvailableStatus
    services: List[ContractorServiceDetail]

    model_config = ConfigDict(from_attributes=True)

class ContractorPublicProfileResponse(BaseModel):
    success: bool = True
    contractor: ContractorPublicProfileDetail
