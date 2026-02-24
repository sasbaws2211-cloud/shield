"""Payment and invoice service with multiple payment method support."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
from app.models.models import Payment, Invoice, JobPosting, User
from fastapi import HTTPException, status
import logging
from decimal import Decimal
import uuid

logger = logging.getLogger(__name__)


class PaymentService:
    """Payment service for handling multiple payment methods."""

    @staticmethod
    def generate_invoice_number(payment_method: str, job_id: str) -> str:
        """Generate unique invoice number per payment method."""
        # Format: METHOD-TIMESTAMP-RANDOM
        # E.g., STR-20260223-123456 (Stripe), BT-20260223-123457 (Bank Transfer), CD-20260223-123458 (Cash)
        method_prefix = {
            "stripe": "STR",
            "bank_transfer": "BT",
            "cash_deposit": "CD"
        }
        prefix = method_prefix.get(payment_method, "INV")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        random_suffix = str(uuid.uuid4())[:8].upper()
        return f"{prefix}-{timestamp}-{random_suffix}"

    @staticmethod
    async def calculate_hours_until_job(db: AsyncSession, job_id: str) -> float:
        """Calculate hours remaining until job starts."""
        result = await db.execute(
            select(JobPosting).where(JobPosting.id == job_id)
        )
        job = result.scalars().first()
        if not job:
            return 0
        hours = (job.start_time - datetime.now(timezone.utc)).total_seconds() / 3600
        return max(0, hours)

    @staticmethod
    async def check_payment_method_requirement(db: AsyncSession, job_id: str) -> dict:
        """Check if Stripe is required for a job based on timing."""
        hours_until_start = await PaymentService.calculate_hours_until_job(db, job_id)

        # Stripe required if less than 72 hours
        stripe_required = hours_until_start < 72
        allowed_methods = ["stripe"] if stripe_required else ["stripe", "bank_transfer", "cash_deposit"]

        return {
            "is_stripe_required": stripe_required,
            "hours_until_start": hours_until_start,
            "allowed_payment_methods": allowed_methods,
            "message": "Stripe payment is COMPULSORY for bookings with less than 72 hours notice" if stripe_required else "Flexible payment methods available"
        }

    @staticmethod
    async def validate_payment_method(db: AsyncSession, job_id: str, payment_method: str) -> bool:
        """Validate if the selected payment method is allowed for the job."""
        requirement = await PaymentService.check_payment_method_requirement(db, job_id)
        if payment_method not in requirement["allowed_payment_methods"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment method '{payment_method}' not allowed for this job. {requirement['message']}"
            )
        return True

    @staticmethod
    async def create_invoice(
        db: AsyncSession,
        job_id: str,
        business_id: str,
        amount_gbp: Decimal,
        payment_method: str,
        due_days: int = 30
    ) -> Invoice:
        """Create an invoice for a job posting."""
        # Validate payment method requirement
        await PaymentService.validate_payment_method(db, job_id, payment_method)

        # Generate unique invoice number
        invoice_number = PaymentService.generate_invoice_number(payment_method, job_id)

        # Set due date
        issued_at = datetime.now(timezone.utc)
        due_at = issued_at + timedelta(days=due_days)

        invoice = Invoice(
            job_id=job_id,
            business_id=business_id,
            invoice_number=invoice_number,
            payment_method=payment_method,
            amount_gbp=amount_gbp,
            status="draft",
            issued_at=issued_at,
            due_at=due_at
        )
        db.add(invoice)
        await db.commit()
        logger.info(f"Invoice created: {invoice_number} for job {job_id} via {payment_method}")
        return invoice

    @staticmethod
    async def issue_invoice(db: AsyncSession, invoice_id: str) -> Invoice:
        """Issue an invoice (change status from draft to issued)."""
        result = await db.execute(
            select(Invoice).where(Invoice.id == invoice_id)
        )
        invoice = result.scalars().first()
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )

        invoice.status = "issued"
        invoice.issued_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info(f"Invoice {invoice.invoice_number} issued")
        return invoice

    @staticmethod
    async def create_payment(
        db: AsyncSession,
        job_id: str,
        business_id: str,
        amount_gbp: Decimal,
        payment_method: str,
        transaction_reference: str = None
    ) -> Payment:
        """Create a payment record."""
        # Validate payment method
        await PaymentService.validate_payment_method(db, job_id, payment_method)

        # Create invoice if not exists
        result = await db.execute(
            select(Invoice).where(
                Invoice.job_id == job_id,
                Invoice.payment_method == payment_method
            )
        )
        existing_invoice = result.scalars().first()

        if not existing_invoice:
            invoice = await PaymentService.create_invoice(db, job_id, business_id, amount_gbp, payment_method)
            await PaymentService.issue_invoice(db, invoice.id)
            invoice_id = invoice.id
        else:
            invoice_id = existing_invoice.id

        # Create payment record
        payment = Payment(
            job_id=job_id,
            business_id=business_id,
            amount_gbp=amount_gbp,
            payment_method=payment_method,
            invoice_id=invoice_id,
            transaction_reference=transaction_reference,
            status="pending"
        )
        db.add(payment)
        await db.commit()
        logger.info(f"Payment created for job {job_id} via {payment_method}")
        return payment

    @staticmethod
    async def mark_payment_complete(
        db: AsyncSession,
        payment_id: str,
        stripe_intent_id: str = None
    ) -> Payment:
        """Mark a payment as completed."""
        result = await db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalars().first()
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        payment.status = "completed"
        payment.completed_at = datetime.now(timezone.utc)
        if stripe_intent_id:
            payment.stripe_payment_intent_id = stripe_intent_id

        # Update job payment status
        job_result = await db.execute(
            select(JobPosting).where(JobPosting.id == payment.job_id)
        )
        job = job_result.scalars().first()
        if job:
            job.payment_status = "paid"
            job.payment_method = payment.payment_method

            # Update invoice status
            invoice_result = await db.execute(
                select(Invoice).where(Invoice.id == payment.invoice_id)
            )
            invoice = invoice_result.scalars().first()
            if invoice:
                invoice.status = "paid"
                invoice.paid_at = datetime.now(timezone.utc)

        await db.commit()
        logger.info(f"Payment {payment_id} marked as complete")
        return payment

    @staticmethod
    async def get_payment_summary(db: AsyncSession, business_id: str) -> dict:
        """Get payment summary by method for a business."""
        result = await db.execute(
            select(Payment).where(
                Payment.business_id == business_id,
                Payment.status != "failed"
            )
        )
        payments = result.scalars().all()

        summary = {
            "total_gbp": Decimal("0"),
            "by_method": {
                "stripe": Decimal("0"),
                "bank_transfer": Decimal("0"),
                "cash_deposit": Decimal("0")
            },
            "pending_gbp": Decimal("0"),
            "completed_gbp": Decimal("0")
        }

        for payment in payments:
            summary["total_gbp"] += payment.amount_gbp
            summary["by_method"][payment.payment_method] += payment.amount_gbp

            if payment.status == "pending":
                summary["pending_gbp"] += payment.amount_gbp
            elif payment.status == "completed":
                summary["completed_gbp"] += payment.amount_gbp

        return summary

    @staticmethod
    async def get_invoices_for_job(db: AsyncSession, job_id: str) -> list:
        """Get all invoices for a job."""
        result = await db.execute(
            select(Invoice).where(Invoice.job_id == job_id)
        )
        return result.scalars().all()

    @staticmethod
    async def retry_payment(db: AsyncSession, payment_id: str) -> Payment:
        """Retry a failed payment."""
        result = await db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalars().first()
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        if payment.status not in ["failed", "pending"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot retry payment with status: {payment.status}"
            )

        payment.status = "pending"
        payment.attempted_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info(f"Payment {payment_id} retry initiated")
        return payment
