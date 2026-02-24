"""Notification orchestration service for triggering emails and notifications."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta
from app.models.models import Payment, Invoice, JobPosting, OfficerShift, User
from app.services.email_service import EmailService
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for orchestrating email notifications based on business events."""

    @staticmethod
    async def trigger_payment_reminder(
        db: AsyncSession,
        invoice_id: str,
        days_before_due: int = 3
    ) -> bool:
        """Trigger payment reminder email for invoice due soon."""
        result = await db.execute(
            select(Invoice).where(Invoice.id == invoice_id)
        )
        invoice = result.scalars().first()
        if not invoice or invoice.status == "paid":
            return False

        user_result = await db.execute(
            select(User).where(User.id == invoice.business_id)
        )
        business = user_result.scalars().first()
        if not business:
            return False

        job_result = await db.execute(
            select(JobPosting).where(JobPosting.id == invoice.job_id)
        )
        job = job_result.scalars().first()
        if not job:
            return False

        due_date_str = invoice.due_at.strftime("%Y-%m-%d") if invoice.due_at else "Not specified"
        payment_method_label = invoice.payment_method.replace("_", " ").title()

        # Send email
        success = EmailService.send_payment_reminder_email(
            business_email=business.billing_email or business.email,
            company_name=business.company_name,
            invoice_number=invoice.invoice_number,
            amount_gbp=float(invoice.amount_gbp),
            payment_method=payment_method_label,
            due_date=due_date_str
        )

        # Queue notification
        if success:
            await EmailService.queue_email_notification(
                db=db,
                recipient_email=business.billing_email or business.email,
                recipient_id=business.id,
                notification_type="payment_reminder",
                subject=f"Payment Reminder - Invoice {invoice.invoice_number}",
                body=f"Invoice {invoice.invoice_number} for £{invoice.amount_gbp} is due on {due_date_str}",
                job_id=invoice.job_id
            )

        return success

    @staticmethod
    async def trigger_shift_confirmation(
        db: AsyncSession,
        shift_id: str
    ) -> bool:
        """Trigger shift confirmation email when a shift is confirmed."""
        result = await db.execute(
            select(OfficerShift).where(OfficerShift.id == shift_id)
        )
        shift = result.scalars().first()
        if not shift or shift.status != "confirmed":
            return False

        user_result = await db.execute(
            select(User).where(User.id == shift.officer_id)
        )
        officer = user_result.scalars().first()
        if not officer:
            return False

        start_time_str = shift.start_time.strftime("%Y-%m-%d %H:%M")
        end_time_str = shift.end_time.strftime("%Y-%m-%d %H:%M")

        success = EmailService.send_shift_confirmation_email(
            officer_email=officer.email,
            officer_name=officer.full_name or "Officer",
            job_title=shift.title,
            site_name=shift.site_name,
            start_time=start_time_str,
            end_time=end_time_str,
            hourly_rate=float(shift.hourly_rate_gbp)
        )

        if success:
            await EmailService.queue_email_notification(
                db=db,
                recipient_email=officer.email,
                recipient_id=officer.id,
                notification_type="shift_confirmation",
                subject=f"Shift Confirmed - {shift.title}",
                body=f"Your shift '{shift.title}' at {shift.site_name} on {start_time_str} is confirmed. Rate: £{shift.hourly_rate_gbp}/hr",
                job_id=shift.job_id
            )

        return success

    @staticmethod
    async def trigger_payday_confirmation(
        db: AsyncSession,
        officer_id: str,
        pay_date: datetime
    ) -> bool:
        """Trigger payday confirmation email the day before payment."""
        result = await db.execute(
            select(User).where(User.id == officer_id)
        )
        officer = result.scalars().first()
        if not officer:
            return False

        # Calculate total payment due
        shifts_result = await db.execute(
            select(OfficerShift).where(
                and_(
                    OfficerShift.officer_id == officer_id,
                    OfficerShift.start_time <= pay_date,
                    OfficerShift.end_time >= pay_date - timedelta(days=7)  # Default weekly
                )
            )
        )
        shifts = shifts_result.scalars().all()

        total_payment = sum(
            float(shift.hourly_rate_gbp) * 
            ((shift.end_time - shift.start_time).total_seconds() / 3600)
            for shift in shifts
        )

        pay_date_str = pay_date.strftime("%Y-%m-%d")

        success = EmailService.send_payday_confirmation_email(
            officer_email=officer.email,
            officer_name=officer.full_name or "Officer",
            payment_amount=total_payment,
            payment_date=pay_date_str,
            payment_method="Bank Transfer"  # Default, can be made configurable
        )

        if success:
            await EmailService.queue_email_notification(
                db=db,
                recipient_email=officer.email,
                recipient_id=officer.id,
                notification_type="payday_confirmation",
                subject=f"Payday Confirmation - £{total_payment}",
                body=f"Payment of £{total_payment} is scheduled for {pay_date_str}",
                scheduled_for=pay_date - timedelta(days=1)  # Schedule for day before
            )

        return success

    @staticmethod
    async def trigger_shift_alert(
        db: AsyncSession,
        shift_id: str,
        hours_before: int = 24
    ) -> bool:
        """Trigger shift alert email hours before shift starts."""
        result = await db.execute(
            select(OfficerShift).where(OfficerShift.id == shift_id)
        )
        shift = result.scalars().first()
        if not shift or shift.status != "confirmed":
            return False

        user_result = await db.execute(
            select(User).where(User.id == shift.officer_id)
        )
        officer = user_result.scalars().first()
        if not officer:
            return False

        start_time_str = shift.start_time.strftime("%Y-%m-%d %H:%M")

        success = EmailService.send_shift_alert_email(
            officer_email=officer.email,
            officer_name=officer.full_name or "Officer",
            job_title=shift.title,
            site_name=shift.site_name,
            start_time=start_time_str
        )

        if success:
            scheduled_time = shift.start_time - timedelta(hours=hours_before)
            await EmailService.queue_email_notification(
                db=db,
                recipient_email=officer.email,
                recipient_id=officer.id,
                notification_type="shift_alert",
                subject=f"Shift Alert - {shift.title} starts in {hours_before} hours",
                body=f"Your shift '{shift.title}' at {shift.site_name} starts at {start_time_str}. Please ensure you're on your way!",
                job_id=shift.job_id,
                scheduled_for=scheduled_time
            )

        return success

    @staticmethod
    async def trigger_payment_received_for_business(
        db: AsyncSession,
        payment_id: str
    ) -> bool:
        """Trigger notification when payment is received from business."""
        result = await db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalars().first()
        if not payment or payment.status != "completed":
            return False

        user_result = await db.execute(
            select(User).where(User.id == payment.business_id)
        )
        business = user_result.scalars().first()
        if not business:
            return False

        job_result = await db.execute(
            select(JobPosting).where(JobPosting.id == payment.job_id)
        )
        job = job_result.scalars().first()
        if not job:
            return False

        # Send confirmation email
        subject = f"Payment Received - £{payment.amount_gbp}"
        body = f"We have received your payment of £{payment.amount_gbp} for job: {job.title}"
        
        await EmailService.queue_email_notification(
            db=db,
            recipient_email=business.billing_email or business.email,
            recipient_id=business.id,
            notification_type="payment_reminder",  # Reusing for confirmation
            subject=subject,
            body=body,
            job_id=job.id
        )

        return True

    @staticmethod
    async def get_pending_notifications_for_batch(db: AsyncSession, limit: int = 50) -> list:
        """Get pending notifications that need to be sent."""
        notifications = await EmailService.get_pending_notifications(db)
        return notifications[:limit]

    @staticmethod
    async def process_pending_notifications(db: AsyncSession) -> dict:
        """Process all pending notifications."""
        notifications = await EmailService.get_pending_notifications(db)
        results = {
            "total": len(notifications),
            "sent": 0,
            "failed": 0,
            "errors": []
        }

        for notification in notifications:
            try:
                # TODO: Integrate with actual email provider (Elastic Mail)
                # For now, just mark as sent
                await EmailService.mark_notification_sent(db, notification.id)
                results["sent"] += 1
                logger.info(f"Processed notification: {notification.id}")
            except Exception as e:
                await EmailService.mark_notification_failed(db, notification.id, str(e))
                results["failed"] += 1
                results["errors"].append({
                    "notification_id": notification.id,
                    "error": str(e)
                })
                logger.error(f"Failed to process notification {notification.id}: {e}")

        return results
