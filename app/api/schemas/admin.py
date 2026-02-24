"""Pydantic schemas for admin endpoints."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class SIABadgeLevelEnum(str, Enum):
    """SIA Badge Level enumeration."""
    SECURITY_GUARD = "security_guard"
    DOOR_SUPERVISOR = "door_supervisor"
    CCTV_OPERATOR = "cctv_operator"
    CLOSE_PROTECTION = "close_protection"


class RegistrationReviewRequest(BaseModel):
    """Admin registration review request."""
    action: str = Field(..., pattern="^(approve|reject)$")
    reject_reason: Optional[str] = Field(None, min_length=10)


class OfficerRegistrationResponse(BaseModel):
    """Officer registration response."""
    id: str
    user_id: str
    full_name: Optional[str]
    email: str
    sia_badge_number: str
    badge_expiry_date: datetime
    sia_badge_level: SIABadgeLevelEnum
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    emergency_contact_relationship: Optional[str]
    risk_level: str
    status: str
    reject_reason: Optional[str]
    submitted_at: datetime
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]

    class Config:
        from_attributes = True


class RegistrationsListResponse(BaseModel):
    """Registrations list response."""
    registrations: List[OfficerRegistrationResponse]
    summary: dict


class JobPostingReviewRequest(BaseModel):
    """Admin job posting review request."""
    action: str = Field(..., pattern="^(accept|reject)$")
    reject_reason: Optional[str] = Field(None, min_length=10)


class JobPostingAdminResponse(BaseModel):
    """Job posting admin response."""
    id: str
    business_id: str
    company_name: str
    title: str
    site_name: str
    start_time: datetime
    end_time: datetime
    guards_required: int
    budget_gbp: Optional[float]
    notes: Optional[str]
    status: str
    reject_reason: Optional[str]
    submitted_at: datetime
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    payment_link_sent_at: Optional[datetime]

    class Config:
        from_attributes = True


class JobPostingsListResponse(BaseModel):
    """Job postings list response."""
    job_postings: List[JobPostingAdminResponse]
    summary: dict
