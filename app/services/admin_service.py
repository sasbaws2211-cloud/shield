"""Admin service with business logic."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from app.models.models import OfficerRegistration, JobPosting, User, AuditLog
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class AdminService:
    """Admin service."""

    @staticmethod
    async def approve_officer_registration(
        db: AsyncSession,
        registration_id: str,
        admin_id: str,
        ip_address: str
    ) -> dict:
        """Approve an officer registration."""
        result = await db.execute(
            select(OfficerRegistration).where(
                OfficerRegistration.id == registration_id
            )
        )
        registration = result.scalars().first()

        if not registration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration not found"
            )

        # Update registration
        registration.status = "approved"
        registration.reviewed_by = admin_id
        registration.reviewed_at = datetime.now(timezone.utc)

        # Query and update user status
        user_result = await db.execute(
            select(User).where(User.id == registration.user_id)
        )
        user = user_result.scalars().first()
        user.status = "approved"

        # Log audit
        audit_log = AuditLog(
            admin_id=admin_id,
            action="approve_officer_registration",
            target_id=registration_id,
            target_type="OfficerRegistration",
            ip_address=ip_address
        )
        db.add(audit_log)
        await db.commit()
        logger.info(f"Officer registration {registration_id} approved by {admin_id}")

        return {
            "id": registration.id,
            "status": "approved",
            "reviewed_at": registration.reviewed_at
        }
    @staticmethod
    async def reject_officer_registration(
        db: AsyncSession,
        registration_id: str,
        reject_reason: str,
        admin_id: str,
        ip_address: str
    ) -> dict:
        """Reject an officer registration."""
        result = await db.execute(
            select(OfficerRegistration).where(
                OfficerRegistration.id == registration_id
            )
        )
        registration = result.scalars().first()

        if not registration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration not found"
            )

        # Update registration
        registration.status = "rejected"
        registration.reject_reason = reject_reason
        registration.reviewed_by = admin_id
        registration.reviewed_at = datetime.now(timezone.utc)

        # Query and update user status
        user_result = await db.execute(
            select(User).where(User.id == registration.user_id)
        )
        user = user_result.scalars().first()
        user.status = "rejected"

        # Log audit
        audit_log = AuditLog(
            admin_id=admin_id,
            action="reject_officer_registration",
            target_id=registration_id,
            target_type="OfficerRegistration",
            details=reject_reason,
            ip_address=ip_address
        )
        db.add(audit_log)
        await db.commit()
        logger.info(f"Officer registration {registration_id} rejected by {admin_id}")

        return {
            "id": registration.id,
            "status": "rejected",
            "reviewed_at": registration.reviewed_at
        }
    @staticmethod
    async def accept_job_posting(
        db: AsyncSession,
        job_id: str,
        admin_id: str,
        ip_address: str
    ) -> dict:
        """Accept a job posting."""
        result = await db.execute(
            select(JobPosting).where(JobPosting.id == job_id)
        )
        job = result.scalars().first()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting not found"
            )

        # Update job
        job.status = "accepted"
        job.reviewed_by = admin_id
        job.reviewed_at = datetime.now(timezone.utc)
        job.payment_link_sent_at = datetime.now(timezone.utc)

        # TODO: Create Stripe payment link and set stripe_payment_link_id

        # Log audit
        audit_log = AuditLog(
            admin_id=admin_id,
            action="accept_job_posting",
            target_id=job_id,
            target_type="JobPosting",
            ip_address=ip_address
        )
        db.add(audit_log)
        await db.commit()
        logger.info(f"Job posting {job_id} accepted by {admin_id}")

        return {
            "id": job.id,
            "status": "accepted",
            "reviewed_at": job.reviewed_at,
            "stripe_payment_url": job.stripe_payment_link_id
        }
    @staticmethod
    async def reject_job_posting(
        db: AsyncSession,
        job_id: str,
        reject_reason: str,
        admin_id: str,
        ip_address: str
    ) -> dict:
        """Reject a job posting."""
        result = await db.execute(
            select(JobPosting).where(JobPosting.id == job_id)
        )
        job = result.scalars().first()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting not found"
            )

        # Update job
        job.status = "rejected"
        job.reject_reason = reject_reason
        job.reviewed_by = admin_id
        job.reviewed_at = datetime.now(timezone.utc)

        # Log audit
        audit_log = AuditLog(
            admin_id=admin_id,
            action="reject_job_posting",
            target_id=job_id,
            target_type="JobPosting",
            details=reject_reason,
            ip_address=ip_address
        )
        db.add(audit_log)
        await db.commit()
        logger.info(f"Job posting {job_id} rejected by {admin_id}")

        return {
            "id": job.id,
            "status": "rejected",
            "reviewed_at": job.reviewed_at
        }
