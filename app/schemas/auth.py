import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class AgreementInput(BaseModel):
    terms_type: str = Field(min_length=1, max_length=50)
    terms_version: str = Field(min_length=1, max_length=20)
    is_agreed: bool


class SignupBase(BaseModel):
    # users.login_id is currently defined as VARCHAR(50) and is populated from email.
    email: EmailStr = Field(max_length=50)
    password: str = Field(min_length=8, max_length=72)
    nickname: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=1, max_length=50)
    phone: str | None = Field(None, max_length=20)
    default_address_json: dict[str, Any] | None = None
    agreements: list[AgreementInput] = Field(min_length=1)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("password must be at most 72 bytes")
        if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
            raise ValueError("password must contain at least one letter and one number")
        return value

    @field_validator("nickname", "name")
    @classmethod
    def trim_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        normalized = re.sub(r"[^0-9+]", "", value)
        if len(re.sub(r"\D", "", normalized)) < 9:
            raise ValueError("invalid phone number")
        return normalized


class CustomerSignupRequest(SignupBase):
    pass


class ContractorSignupRequest(SignupBase):
    business_name: str = Field(min_length=1, max_length=100)
    representative_name: str = Field(min_length=1, max_length=50)
    contact_phone: str = Field(min_length=9, max_length=20)
    business_status: str = Field(min_length=1, max_length=20)
    business_number: str | None = Field(None, max_length=20)

    @field_validator("business_name", "representative_name", "business_status")
    @classmethod
    def trim_contractor_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("contact_phone")
    @classmethod
    def normalize_contact_phone(cls, value: str) -> str:
        normalized = re.sub(r"[^0-9+]", "", value)
        if len(re.sub(r"\D", "", normalized)) < 9:
            raise ValueError("invalid contact phone number")
        return normalized


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class LogoutRequest(RefreshRequest):
    pass


class SignupResponse(BaseModel):
    success: bool = True
    user_id: int
    user_type: Literal["CUSTOMER", "CONTRACTOR", "BOTH"]
    contractor_id: int | None = None
    approval_status: str | None = None
    created_at: datetime


class AuthUser(BaseModel):
    user_id: int
    nickname: str
    user_type: str


class LoginResponse(BaseModel):
    success: bool = True
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: AuthUser


class RefreshResponse(BaseModel):
    success: bool = True
    access_token: str
    expires_in: int
    refresh_token: str | None = None


class AvailabilityResponse(BaseModel):
    success: bool = True
    available: bool


class MessageResponse(BaseModel):
    success: bool = True
    message: str


class AgreementResponse(BaseModel):
    terms_type: str
    terms_version: str
    terms_title: str
    terms_content_url: str
    is_required: bool

    model_config = ConfigDict(from_attributes=True)


class AgreementListResponse(BaseModel):
    success: bool = True
    agreements: list[AgreementResponse]
