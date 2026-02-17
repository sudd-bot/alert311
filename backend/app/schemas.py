"""
Pydantic schemas for API request/response validation.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import re


# ============ User Schemas ============

class AccountType(str, Enum):
    FREE = "free"
    PAID = "paid"


class UserRegister(BaseModel):
    phone: str = Field(..., description="Phone number in E.164 format (e.g., +16464171584)")
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate phone number is in E.164 format."""
        # E.164 format: +[country code][number]
        # Example: +16464171584
        if not re.match(r'^\+[1-9]\d{1,14}$', v):
            raise ValueError(
                "Phone number must be in E.164 format (e.g., +16464171584). "
                "Include country code with + prefix."
            )
        return v


class UserVerify(BaseModel):
    phone: str
    code: str = Field(..., description="6-digit verification code")


class UserResponse(BaseModel):
    id: int
    phone: str
    verified: bool
    account_type: AccountType
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Alert Schemas ============

class AlertCreate(BaseModel):
    address: str = Field(..., min_length=5, description="Street address in San Francisco")
    report_type_id: Optional[str] = Field(None, description="311 ticket type ID (defaults to parking on sidewalk)")
    
    @field_validator('address')
    @classmethod
    def validate_address(cls, v: str) -> str:
        """Validate address is not empty or just whitespace."""
        v = v.strip()
        if not v:
            raise ValueError("Address cannot be empty")
        return v


class AlertUpdate(BaseModel):
    active: bool


class AlertResponse(BaseModel):
    id: int
    address: str
    latitude: float
    longitude: float
    report_type_id: str
    report_type_name: str
    active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Report Schemas ============

class ReportResponse(BaseModel):
    id: int
    report_id: str
    report_data: dict
    sms_sent: bool
    created_at: datetime
    alert_id: int
    
    class Config:
        from_attributes = True


# ============ General Responses ============

class SuccessResponse(BaseModel):
    success: bool
    message: str
    already_verified: Optional[bool] = False


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
