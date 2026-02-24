"""Job service with business logic."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
from app.models.models import JobPosting, JobApplication, OfficerShift, User, Payment, Invoice
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class JobService:
    """Job service with async database operations."""

    @staticmethod
    def validate_job_posting(start_time: datetime, end_time: datetime) -> dict:
        """Validate job posting times and return payment requirement info."""
        now = datetime.now(timezone.utc)

        # Check if start time is in future
        if start_time <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start time must be in the future"
            )

        # Check if end time is after start time
        if end_time <= start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End time must be after start time"
            )

        # Check hours until start
        hours_until_start = (start_time - now).total_seconds() / 3600

        # Determine if Stripe is required (less than 72 hours)
        stripe_required = hours_until_start < 72
        allowed_methods = ["stripe"] if stripe_required else ["stripe", "bank_transfer", "cash_deposit"]

        return {
            "stripe_required": stripe_required,
            "hours_until_start": hours_until_start,
            "allowed_payment_methods": allowed_methods,
            "message": "Stripe payment required for last-minute bookings (< 72 hours)" if stripe_required else "Flexible payment methods available"
        }

    @staticmethod
    async def validate_badge_level_match(db: AsyncSession, officer_id: str, required_badge_level: str) -> bool:
        """Validate if officer's badge level matches job requirement."""
        result = await db.execute(select(User).where(User.id == officer_id))
        officer = result.scalars().first()
        
        if not officer or not officer.sia_badge_level:
            return False

        # Badge level hierarchy: door_supervisor covers most roles
        if officer.sia_badge_level == "door_supervisor":
            return True

        # Other badges must match exactly
        return officer.sia_badge_level == required_badge_level

    @staticmethod
    async def create_job_posting(
        db: AsyncSession,
        business_id: str,
        title: str,
        site_name: str,
        site_address: str,
        start_time: datetime,
        end_time: datetime,
        guards_required: int,
        required_badge_level: str = "door_supervisor",
        notes: str = None,
        budget_gbp: float = None
    ) -> dict:
        """Create a new job posting with payment requirement validation."""
        # Validate times and get payment info
        payment_info = JobService.validate_job_posting(start_time, end_time)

        # Create job posting
        job = JobPosting(
            business_id=business_id,
            title=title,
            site_name=site_name,
            site_address=site_address,
            start_time=start_time,
            end_time=end_time,
            guards_required=guards_required,
            required_badge_level=required_badge_level,
            notes=notes,
            budget_gbp=budget_gbp,
            status="pending",
            payment_status="pending"
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        
        logger.info(f"Job posting created: {job.id} - Badge level: {required_badge_level}")
        return {
            "job_id": job.id,
            "status": "pending",
            "message": "Your job request has been submitted and is pending admin review.",
            "payment_info": payment_info
        }

    @staticmethod
    async def check_time_conflict(
        db: AsyncSession,
        officer_id: str,
        job_start: datetime,
        job_end: datetime
    ) -> bool:
        """Check if officer has conflicting shifts."""
        result = await db.execute(
            select(OfficerShift).where(
                OfficerShift.officer_id == officer_id,
                OfficerShift.status == "confirmed",
                OfficerShift.start_time < job_end,
                OfficerShift.end_time > job_start
            )
        )
        conflict = result.scalars().first()
        return conflict is not None

    @staticmethod
    async def check_badge_expiry(
        db: AsyncSession,
        officer_id: str,
        job_start: datetime
    ) -> bool:
        """Check if officer's badge is valid for job date. Returns True if EXPIRED."""
        result = await db.execute(select(User).where(User.id == officer_id))
        officer = result.scalars().first()
        
        if not officer or not officer.badge_expiry_date:
            return True  # No badge = expired

        # Return True if badge expires before job starts
        return officer.badge_expiry_date.date() < job_start.date()

    @staticmethod
    async def get_available_slots(
        db: AsyncSession,
        job_id: str
    ) -> int:
        """Get available guard slots for a job."""
        result = await db.execute(select(JobPosting).where(JobPosting.id == job_id))
        job = result.scalars().first()
        
        if not job:
            return 0

        confirmed_result = await db.execute(
            select(JobApplication).where(
                JobApplication.job_id == job_id,
                JobApplication.status == "confirmed"
            )
        )
        confirmed_count = len(confirmed_result.scalars().all())
        return job.guards_required - confirmed_count

    @staticmethod
    async def apply_to_job(
        db: AsyncSession,
        job_id: str,
        officer_id: str
    ) -> dict:
        """Apply officer to a job posting with full validation."""
        # Check if job exists and is accepted
        result = await db.execute(select(JobPosting).where(JobPosting.id == job_id))
        job = result.scalars().first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        if job.status != "accepted":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Job is not available for applications"
            )

        # Check if already applied
        existing_result = await db.execute(
            select(JobApplication).where(
                JobApplication.job_id == job_id,
                JobApplication.officer_id == officer_id
            )
        )
        existing_application = existing_result.scalars().first()

        if existing_application:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already applied for this job"
            )

        # Check badge expiry
        if await JobService.check_badge_expiry(db, officer_id, job.start_time):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Your SIA badge expires before this shift date"
            )

        # Check badge level match
        if not await JobService.validate_badge_level_match(db, officer_id, job.required_badge_level):
            officer_result = await db.execute(select(User).where(User.id == officer_id))
            officer = officer_result.scalars().first()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Your badge level ({officer.sia_badge_level}) does not match the required level ({job.required_badge_level}). "
                       f"Door Supervisor badge can fulfill most roles."
            )

        # Check time conflict
        if await JobService.check_time_conflict(db, officer_id, job.start_time, job.end_time):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="You have a confirmed shift that overlaps with this job"
            )

        # Check available slots
        if await JobService.get_available_slots(db, job_id) <= 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="All guard positions for this job have been filled"
            )

        # Create application
        application = JobApplication(
            job_id=job_id,
            officer_id=officer_id,
            status="applied"
        )
        db.add(application)
        await db.commit()
        await db.refresh(application)
        
        logger.info(f"Officer {officer_id} applied to job {job_id} - Badge level: {job.required_badge_level}")
        return {
            "application_id": application.id,
            "status": "applied",
            "applied_at": application.applied_at
        }

    @staticmethod
    async def confirm_application(
        db: AsyncSession,
        application_id: str
    ) -> None:
        """Confirm a job application and create shift."""
        result = await db.execute(
            select(JobApplication).where(JobApplication.id == application_id)
        )
        application = result.scalars().first()

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )

        # Update application status
        application.status = "confirmed"

        # Get job details
        job_result = await db.execute(
            select(JobPosting).where(JobPosting.id == application.job_id)
        )
        job = job_result.scalars().first()

        # Calculate hourly rate
        duration_hours = (job.end_time - job.start_time).total_seconds() / 3600
        hourly_rate = float(job.budget_gbp) / (job.guards_required * duration_hours) if job.budget_gbp else 0

        # Create officer shift
        shift = OfficerShift(
            officer_id=application.officer_id,
            job_id=application.job_id,
            application_id=application.id,
            title=job.title,
            site_name=job.site_name,
            start_time=job.start_time,
            end_time=job.end_time,
            hourly_rate_gbp=hourly_rate,
            status="confirmed"
        )
        db.add(shift)
        await db.commit()

     
