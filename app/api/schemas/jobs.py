"""Pydantic schemas for job-related endpoints."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from enum import Enum


class SIABadgeLevelEnum(str, Enum):
    """SIA Badge Level enumeration."""
    SECURITY_GUARD = "security_guard"
    DOOR_SUPERVISOR = "door_supervisor"
    CCTV_OPERATOR = "cctv_operator"
    CLOSE_PROTECTION = "close_protection"


class JobPostingCreateRequest(BaseModel):
    """Job posting creation request."""
    title: str = Field(..., min_length=1, max_length=255)
    site_name: str = Field(..., min_length=1, max_length=255)
    site_address: str
    start_time: datetime
    end_time: datetime
    guards_required: int = Field(..., ge=1)
    required_badge_level: Optional[SIABadgeLevelEnum] = Field(default="door_supervisor", description="Required SIA badge level for this job")
    notes: Optional[str] = None
    budget_gbp: Optional[Decimal] = None


class JobPostingResponse(BaseModel):
    """Job posting response."""
    id: str
    business_id: str
    title: str
    site_name: str
    site_address: Optional[str]
    start_time: datetime
    end_time: datetime
    guards_required: int
    required_badge_level: SIABadgeLevelEnum
    notes: Optional[str]
    budget_gbp: Optional[Decimal]
    status: str
    payment_method: Optional[str] = None
    payment_status: str
    submitted_at: datetime
    hourly_rate_gbp: Optional[Decimal] = None

    class Config:
        from_attributes = True


class JobPoolResponse(BaseModel):
    """Job pool response."""
    jobs: List[JobPostingResponse]
    pagination: dict


class JobApplicationResponse(BaseModel):
    """Job application response."""
    application_id: str
    status: str
    applied_at: datetime


class OfficerShiftResponse(BaseModel):
    """Officer shift response."""
    id: str
    job_id: str
    title: str
    site_name: str
    start_time: datetime
    end_time: datetime
    hourly_rate_gbp: Decimal
    status: str

    class Config:
        from_attributes = True


class OfficerShiftsResponse(BaseModel):
    """Officer shifts response."""
    shifts: List[OfficerShiftResponse]


class BusinessJobRequestsResponse(BaseModel):
    """Business job requests response."""
    job_requests: List[JobPostingResponse]


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    message: str
    details: Optional[dict] = None
