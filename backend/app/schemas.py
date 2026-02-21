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
    phone: str = Field(..., description="Phone number (e.g., 646-417-1584)")
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """
        Normalize and validate phone number to E.164 format.
        Handles inputs like "646-417-1584", "(646) 417-1584", "6464171584",
        "16464171584", "+16464171584".
        """
        v = v.strip()
        digits = re.sub(r'\D', '', v)

        # Already has a + country code prefix — return as +DIGITS
        if v.startswith('+') and len(digits) >= 7:
            return f"+{digits}"

        # 10-digit US number (no country code)
        if len(digits) == 10:
            return f"+1{digits}"

        # 11-digit number starting with 1 (US with country code, no +)
        if len(digits) == 11 and digits.startswith('1'):
            return f"+{digits}"

        # Invalid format
        raise ValueError(
            "Invalid phone number format. Please enter a 10-digit US number "
            "(e.g., 646-417-1584 or (646) 417-1584)."
        )


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
    address: str = Field(..., min_length=5, max_length=500, description="Street address in San Francisco")
    report_type_id: Optional[str] = Field(None, description="311 ticket type ID (defaults to parking on sidewalk)")
    # Optional pre-computed coordinates from the frontend (map geocoder).
    # When provided, the backend skips the geocoding API call — faster and cheaper.
    latitude: Optional[float] = Field(None, description="Latitude from frontend geocoder (skip re-geocoding if provided)")
    longitude: Optional[float] = Field(None, description="Longitude from frontend geocoder (skip re-geocoding if provided)")

    @field_validator('address')
    @classmethod
    def validate_address(cls, v: str) -> str:
        """Validate address is not empty or just whitespace."""
        v = v.strip()
        if not v:
            raise ValueError("Address cannot be empty")
        # Remove excessive whitespace within the address
        import re
        v = re.sub(r'\s+', ' ', v)
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
