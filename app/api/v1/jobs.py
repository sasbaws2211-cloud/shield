"""Job posting and application endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import get_current_officer, get_current_business
from app.models.models import User, JobPosting, OfficerShift
from app.api.schemas.jobs import (
    JobPostingCreateRequest,
    JobPostingResponse,
    JobPoolResponse,
    JobApplicationResponse,
    OfficerShiftsResponse,
    BusinessJobRequestsResponse,
)
from app.services.job_service import JobService
from app.services.email_service import EmailService
from decimal import Decimal

jobs_router = APIRouter()


@jobs_router.get("/jobs/pool", response_model=JobPoolResponse)
async def get_job_pool(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_officer),
    db: AsyncSession = Depends(get_db)
):
    """Get all accepted job postings for officers."""
    # Query accepted jobs
    result = await db.execute(
        select(JobPosting)
        .where(JobPosting.status == "accepted")
        .offset((page - 1) * limit)
        .limit(limit)
    )
    jobs = result.scalars().all()
    
    # Get total count
    total_result = await db.execute(select(JobPosting).where(JobPosting.status == "accepted"))
    total = len(total_result.scalars().all())
    
    job_responses = []
    for job in jobs:
        # Calculate hourly rate
        duration_hours = (job.end_time - job.start_time).total_seconds() / 3600
        hourly_rate = float(job.budget_gbp) / (job.guards_required * duration_hours) if job.budget_gbp else None
        job_responses.append(JobPostingResponse(
            id=job.id,
            business_id=job.business_id,
            title=job.title,
            site_name=job.site_name,
            site_address=job.site_address,
            start_time=job.start_time,
            end_time=job.end_time,
            guards_required=job.guards_required,
            notes=job.notes,
            budget_gbp=job.budget_gbp,
            status=job.status,
            submitted_at=job.submitted_at,
            hourly_rate_gbp=hourly_rate
        ))
    
    return JobPoolResponse(
        jobs=job_responses,
        pagination={
            "page": page,
            "limit": limit,
            "total": total
        }
    )


@jobs_router.post("/jobs/{job_id}/apply", response_model=JobApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_to_job(
    job_id: str,
    current_user: User = Depends(get_current_officer),
    db: AsyncSession = Depends(get_db)
):
    """Apply officer to a job posting."""
    result = await JobService.apply_to_job(db=db, job_id=job_id, officer_id=current_user.id)
    return JobApplicationResponse(
        application_id=result["application_id"],
        status=result["status"],
        applied_at=result["applied_at"]
    )


@jobs_router.get("/officer/shifts", response_model=OfficerShiftsResponse)
async def get_officer_shifts(
    current_user: User = Depends(get_current_officer),
    db: AsyncSession = Depends(get_db)
):
    """Get officer's confirmed shifts."""
    result = await db.execute(
        select(OfficerShift).where(
            OfficerShift.officer_id == current_user.id,
            OfficerShift.status == "confirmed"
        )
    )
    shifts = result.scalars().all()
    return OfficerShiftsResponse(shifts=shifts)


@jobs_router.post("/business/job-requests", status_code=status.HTTP_201_CREATED)
async def create_job_request(
    request: JobPostingCreateRequest,
    current_user: User = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Create a new job posting request."""
    result = await JobService.create_job_posting(
        db=db,
        business_id=current_user.id,
        title=request.title,
        site_name=request.site_name,
        site_address=request.site_address,
        start_time=request.start_time,
        end_time=request.end_time,
        guards_required=request.guards_required,
        notes=request.notes,
        budget_gbp=float(request.budget_gbp) if request.budget_gbp else None
    )
    
    # Send admin notification (fire and forget)
    EmailService.send_admin_notification_email(
        admin_email="admin@swiftshield.com",
        subject="New Job Posting",
        message=f"New job posting from {current_user.company_name}: {request.title}"
    )
    
    return result


@jobs_router.get("/business/job-requests", response_model=BusinessJobRequestsResponse)
async def get_business_job_requests(
    current_user: User = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Get all job requests submitted by business."""
    result = await db.execute(
        select(JobPosting).where(JobPosting.business_id == current_user.id)
    )
    job_requests = result.scalars().all()
    return BusinessJobRequestsResponse(job_requests=job_requests)


@jobs_router.post("/applications/{application_id}/confirm", status_code=status.HTTP_200_OK)
async def confirm_application(
    application_id: str,
    current_user: User = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Confirm a job application and create shift."""
    await JobService.confirm_application(db=db, application_id=application_id)
    
    return {
        "message": "Application confirmed successfully",
        "application_id": application_id
    }
