"""Pydantic schemas for authentication endpoints."""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class SIABadgeLevelEnum(str, Enum):
    """SIA Badge Level enumeration."""
    SECURITY_GUARD = "security_guard"
    DOOR_SUPERVISOR = "door_supervisor"
    CCTV_OPERATOR = "cctv_operator"
    CLOSE_PROTECTION = "close_protection"


class OfficerRegisterRequest(BaseModel):
    """Officer registration request."""
    full_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    sia_badge_number: str = Field(..., pattern=r"^SIA-\d{7}$")
    badge_expiry_date: datetime
    sia_badge_level: SIABadgeLevelEnum
    emergency_contact_name: Optional[str] = Field(None, min_length=1, max_length=255)
    emergency_contact_phone: Optional[str] = Field(None, pattern=r"^\+?[0-9]{10,15}$")
    emergency_contact_relationship: Optional[str] = Field(None, min_length=1, max_length=100)


class BusinessRegisterRequest(BaseModel):
    """Business registration request."""
    company_name: str = Field(..., min_length=1, max_length=255)
    contact_person: str = Field(..., min_length=1, max_length=255)
    billing_email: EmailStr
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    """Login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User response."""
    id: str
    role: str
    email: str
    status: str
    full_name: Optional[str] = None
    sia_badge_number: Optional[str] = None
    sia_badge_level: Optional[SIABadgeLevelEnum] = None
    badge_expiry_date: Optional[datetime] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    company_name: Optional[str] = None
    contact_person: Optional[str] = None

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Login response."""
    access_token: str
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Refresh token response."""
    access_token: str


class RegistrationResponse(BaseModel):
    """Registration response."""
    message: str
    registration_id: str
