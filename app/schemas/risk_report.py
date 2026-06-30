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
    risk_score: int
    risk_level: str
    summary: str
    risk_items: list[dict[str, Any]] | None = None
    checklist: list[dict[str, Any]] | None = None
    additional_cost_risks: list[dict[str, Any]] | None = None
    safety_risks: list[dict[str, Any]] | None = None
    contract_risks: list[dict[str, Any]] | None = None
    field_variable_risks: list[dict[str, Any]] | None = None
    sources: list[dict[str, Any]] = []
    created_at: datetime
    completed_at: datetime | None = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RiskReportDetailResponse(BaseModel):
    success: bool = True
    report: RiskReportDetail
