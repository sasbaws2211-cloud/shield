"""Admin endpoints for managing registrations and job postings."""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.models.models import User, OfficerRegistration, JobPosting
from app.api.schemas.admin import (
    RegistrationReviewRequest,
    OfficerRegistrationResponse,
    RegistrationsListResponse,
    JobPostingReviewRequest,
    JobPostingAdminResponse,
    JobPostingsListResponse,
)
from app.services.admin_service import AdminService
from app.services.email_service import EmailService
from app.services.stripe_service import StripeService

admin_router = APIRouter()


@admin_router.get("/registrations", response_model=RegistrationsListResponse)
async def list_registrations(
    status: str = Query("all", pattern="^(pending|approved|rejected|all)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """List officer registrations with optional filtering."""
    query = select(OfficerRegistration)
    
    if status != "all":
        # This select needs to be adjusted for async
        result = await db.execute(
            select(OfficerRegistration).where(OfficerRegistration.status == status)
            .offset((page - 1) * limit)
            .limit(limit)
        )
        registrations = result.scalars().all()
    else:
        result = await db.execute(
            select(OfficerRegistration)
            .offset((page - 1) * limit)
            .limit(limit)
        )
        registrations = result.scalars().all()
    
    # Get summary counts
    pending_result = await db.execute(
        select(OfficerRegistration).where(OfficerRegistration.status == "pending")
    )
    approved_result = await db.execute(
        select(OfficerRegistration).where(OfficerRegistration.status == "approved")
    )
    rejected_result = await db.execute(
        select(OfficerRegistration).where(OfficerRegistration.status == "rejected")
    )
    
    total_result = await db.execute(select(OfficerRegistration))
    total = len(total_result.scalars().all())
    
    summary = {
        "pending": len(pending_result.scalars().all()),
        "approved": len(approved_result.scalars().all()),
        "rejected": len(rejected_result.scalars().all()),
        "total": total
    }
    
    registration_responses = []
    for reg in registrations:
        user_result = await db.execute(select(User).where(User.id == reg.user_id))
        user = user_result.scalars().first()
        registration_responses.append(OfficerRegistrationResponse(
            id=reg.id,
            user_id=reg.user_id,
            full_name=user.full_name if user else None,
            email=user.email if user else None,
            sia_badge_number=reg.sia_badge_number,
            badge_expiry_date=reg.badge_expiry_date,
            risk_level=reg.risk_level,
            status=reg.status,
            reject_reason=reg.reject_reason,
            submitted_at=reg.submitted_at,
            reviewed_by=reg.reviewed_by,
            reviewed_at=reg.reviewed_at
        ))
    
    return RegistrationsListResponse(
        registrations=registration_responses,
        summary=summary
    )


@admin_router.patch("/registrations/{registration_id}")
async def review_registration(
    registration_id: str,
    request: RegistrationReviewRequest,
    http_request: Request,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Approve or reject an officer registration."""
    ip_address = http_request.client.host if http_request.client else "unknown"
    
    if request.action == "approve":
        result = await AdminService.approve_officer_registration(
            db=db,
            registration_id=registration_id,
            admin_id=current_user.id,
            ip_address=ip_address
        )
        
        # Send approval email
        reg_result = await db.execute(
            select(OfficerRegistration).where(OfficerRegistration.id == registration_id)
        )
        registration = reg_result.scalars().first()
        user_result = await db.execute(select(User).where(User.id == registration.user_id))
        user = user_result.scalars().first()
        
        EmailService.send_officer_approved_email(
            officer_email=user.email,
            officer_name=user.full_name
        )
    else:
        if not request.reject_reason or len(request.reject_reason) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reject reason must be at least 10 characters"
            )
        
        result = await AdminService.reject_officer_registration(
            db=db,
            registration_id=registration_id,
            reject_reason=request.reject_reason,
            admin_id=current_user.id,
            ip_address=ip_address
        )
        
        # Send rejection email
        reg_result = await db.execute(
            select(OfficerRegistration).where(OfficerRegistration.id == registration_id)
        )
        registration = reg_result.scalars().first()
        user_result = await db.execute(select(User).where(User.id == registration.user_id))
        user = user_result.scalars().first()
        
        EmailService.send_officer_rejected_email(
            officer_email=user.email,
            officer_name=user.full_name,
            reject_reason=request.reject_reason
        )
    
    return result


@admin_router.get("/job-postings", response_model=JobPostingsListResponse)
async def list_job_postings(
    status: str = Query("all", pattern="^(pending|accepted|rejected|all)$"),
    company: str = Query(""),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """List job postings with optional filtering."""
    if status != "all":
        if company:
            # Filter by status and company name
            result = await db.execute(
                select(JobPosting)
                .where(JobPosting.status == status)
                .offset((page - 1) * limit)
                .limit(limit)
            )
        else:
            result = await db.execute(
                select(JobPosting)
                .where(JobPosting.status == status)
                .offset((page - 1) * limit)
                .limit(limit)
            )
    else:
        result = await db.execute(
            select(JobPosting)
            .offset((page - 1) * limit)
            .limit(limit)
        )
    
    job_postings = result.scalars().all()
    
    # Get summary counts
    pending_result = await db.execute(
        select(JobPosting).where(JobPosting.status == "pending")
    )
    accepted_result = await db.execute(
        select(JobPosting).where(JobPosting.status == "accepted")
    )
    rejected_result = await db.execute(
        select(JobPosting).where(JobPosting.status == "rejected")
    )
    
    total_result = await db.execute(select(JobPosting))
    total = len(total_result.scalars().all())
    
    summary = {
        "pending": len(pending_result.scalars().all()),
        "accepted": len(accepted_result.scalars().all()),
        "rejected": len(rejected_result.scalars().all()),
        "total": total
    }
    
    posting_responses = []
    for posting in job_postings:
        business_result = await db.execute(select(User).where(User.id == posting.business_id))
        business = business_result.scalars().first()
        posting_responses.append(JobPostingAdminResponse(
            id=posting.id,
            business_id=posting.business_id,
            company_name=business.company_name if business else None,
            title=posting.title,
            site_name=posting.site_name,
            start_time=posting.start_time,
            end_time=posting.end_time,
            guards_required=posting.guards_required,
            budget_gbp=float(posting.budget_gbp) if posting.budget_gbp else None,
            notes=posting.notes,
            status=posting.status,
            reject_reason=posting.reject_reason,
            submitted_at=posting.submitted_at,
            reviewed_by=posting.reviewed_by,
            reviewed_at=posting.reviewed_at,
            payment_link_sent_at=posting.payment_link_sent_at
        ))
    
    return JobPostingsListResponse(
        job_postings=posting_responses,
        summary=summary
    )


@admin_router.patch("/job-postings/{job_id}")
async def review_job_posting(
    job_id: str,
    request: JobPostingReviewRequest,
    http_request: Request,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Accept or reject a job posting."""
    ip_address = http_request.client.host if http_request.client else "unknown"
    
    if request.action == "accept":
        result = await AdminService.accept_job_posting(
            db=db,
            job_id=job_id,
            admin_id=current_user.id,
            ip_address=ip_address
        )
        
        # Get job details
        job_result = await db.execute(select(JobPosting).where(JobPosting.id == job_id))
        job = job_result.scalars().first()
        
        # Create Stripe payment link
        try:
            stripe_result = StripeService.create_payment_link(
                job_id=job_id,
                business_id=job.business_id,
                job_title=job.title,
                amount_gbp=float(job.budget_gbp) if job.budget_gbp else 0
            )
            job.stripe_payment_link_id = stripe_result["payment_link_id"]
            await db.commit()
            result["stripe_payment_url"] = stripe_result["payment_url"]
        except Exception as e:
            # Log error but don't fail the request
            pass
        
        # Send acceptance email
        business_result = await db.execute(select(User).where(User.id == job.business_id))
        business = business_result.scalars().first()
        
        EmailService.send_job_accepted_email(
            business_email=business.billing_email,
            company_name=business.company_name,
            job_title=job.title,
            start_time=job.start_time.isoformat(),
            end_time=job.end_time.isoformat(),
            guards_required=job.guards_required,
            budget_gbp=float(job.budget_gbp) if job.budget_gbp else 0,
            payment_url=result.get("stripe_payment_url")
        )
    else:
        if not request.reject_reason or len(request.reject_reason) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reject reason must be at least 10 characters"
            )
        
        result = await AdminService.reject_job_posting(
            db=db,
            job_id=job_id,
            reject_reason=request.reject_reason,
            admin_id=current_user.id,
            ip_address=ip_address
        )
        
        # Send rejection email
        job_result = await db.execute(select(JobPosting).where(JobPosting.id == job_id))
        job = job_result.scalars().first()
        business_result = await db.execute(select(User).where(User.id == job.business_id))
        business = business_result.scalars().first()
        
        EmailService.send_job_rejected_email(
            business_email=business.billing_email,
            company_name=business.company_name,
            job_title=job.title,
            reject_reason=request.reject_reason
        )
    
    return result
