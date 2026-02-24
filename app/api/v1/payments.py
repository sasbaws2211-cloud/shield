"""Payment management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal
from app.core.database import get_db
from app.core.dependencies import get_current_business, get_current_officer
from app.models.models import Payment, Invoice, User
from app.api.schemas.payment import (
    PaymentCreateRequest,
    PaymentResponse,
    InvoiceResponse,
    PaymentSummaryResponse,
)
from app.services.payment_service import PaymentService
import logging

logger = logging.getLogger(__name__)

pay_router = APIRouter()


@pay_router.post("/create", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    request: PaymentCreateRequest,
    current_user: User = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Create a new payment for a job posting."""
    result = await PaymentService.create_payment(
        db=db,
        job_id=request.job_id,
        business_id=current_user.id,
        amount_gbp=Decimal(str(request.amount_gbp)),
        payment_method=request.payment_method,
        transaction_reference=request.transaction_reference
    )
    
    return PaymentResponse(
        id=result.id,
        job_id=result.job_id,
        business_id=result.business_id,
        amount_gbp=float(result.amount_gbp),
        payment_method=result.payment_method,
        status=result.status,
        created_at=result.created_at,
        completed_at=result.completed_at
    )


@pay_router.post("/{payment_id}/mark-complete", response_model=PaymentResponse)
async def mark_payment_complete(
    payment_id: str,
    stripe_intent_id: str = None,
    current_user: User = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Mark a payment as completed."""
    result = await PaymentService.mark_payment_complete(
        db=db,
        payment_id=payment_id,
        stripe_intent_id=stripe_intent_id
    )
    
    return PaymentResponse(
        id=result.id,
        job_id=result.job_id,
        business_id=result.business_id,
        amount_gbp=float(result.amount_gbp),
        payment_method=result.payment_method,
        status=result.status,
        created_at=result.created_at,
        completed_at=result.completed_at
    )


@pay_router.get("/summary/{business_id}", response_model=PaymentSummaryResponse)
async def get_payment_summary(
    business_id: str,
    current_user: User = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Get payment summary for a business."""
    # Verify user is checking their own summary or is admin
    if current_user.id != business_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access payment summary for another user"
        )
    
    summary = await PaymentService.get_payment_summary(db, business_id)
    
    return PaymentSummaryResponse(
        business_id=business_id,
        total_gbp=float(summary["total_gbp"]),
        by_method=summary["by_method"],
        pending_gbp=float(summary["pending_gbp"]),
        completed_gbp=float(summary["completed_gbp"])
    )


@pay_router.get("/invoices/{job_id}", response_model=list[InvoiceResponse])
async def get_job_invoices(
    job_id: str,
    current_user: User = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Get all invoices for a specific job."""
    invoices = await PaymentService.get_invoices_for_job(db, job_id)
    
    # Verify user owns the job
    if current_user.role == "business":
        from app.models.models import JobPosting
        result = await db.execute(select(JobPosting).where(JobPosting.id == job_id))
        job = result.scalars().first()
        if not job or job.business_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access invoices for this job"
            )
    
    return [
        InvoiceResponse(
            id=invoice.id,
            job_id=invoice.job_id,
            invoice_number=invoice.invoice_number,
            amount_gbp=float(invoice.amount_gbp),
            payment_method=invoice.payment_method,
            status=invoice.status,
            issued_at=invoice.issued_at,
            due_at=invoice.due_at,
            paid_at=invoice.paid_at
        )
        for invoice in invoices
    ]


@pay_router.post("/{payment_id}/retry", response_model=PaymentResponse)
async def retry_payment(
    payment_id: str,
    current_user: User = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Retry a failed payment."""
    result = await PaymentService.retry_payment(db, payment_id)
    
    return PaymentResponse(
        id=result.id,
        job_id=result.job_id,
        business_id=result.business_id,
        amount_gbp=float(result.amount_gbp),
        payment_method=result.payment_method,
        status=result.status,
        created_at=result.created_at,
        completed_at=result.completed_at
    )
