from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

class RiskReportCreateRequest(BaseModel):
    estimate_id: int = Field(gt=0)

class RiskReportCreateResponse(BaseModel):
    success:bool=True
    risk_report_id:int
    report_status:str
    created_at: datetime

class RiskReportListItem(BaseModel):
    risk_report_id: int 
    estimate_id: int 
    report_status: str 
    risk_score: int | None = None 
    risk_level: str | None = None
    summary: str | None = None 
    created_at: datetime 
    completed_at : datetime | None = None 

    model_config = ConfigDict(from_attributes=True)

class RiskReportListResponse(BaseModel):
    success: bool = True 
    items : list[RiskReportListItem]
    page : int 
    size : int 
    total : int     

class RiskReportDetail(BaseModel):
    risk_report_id: int
    estimate_id: int
    report_status: str
    risk_score: int | None = None
    risk_level: str | None = None
    summary: str | None = None
    result_json: dict[str, Any] | None = None
    sources_json: list[dict[str, Any]] | None = None
    created_at: datetime
    completed_at: datetime | None = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RiskReportDetailResponse(BaseModel):
    success: bool = True
    report: RiskReportDetail
