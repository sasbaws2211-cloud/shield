"""Notification management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_admin, get_current_officer, get_current_business
from app.models.models import User, Invoice, OfficerShift, Payment
from app.services.notification_service import NotificationService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

notif_router = APIRouter()


@notif_router.post("/payment-reminder/{invoice_id}", status_code=status.HTTP_200_OK)
async def trigger_payment_reminder(
    invoice_id: str,
    days_before_due: int = Query(3, ge=1, le=30),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Trigger a payment reminder email for an invoice."""
    result = await NotificationService.trigger_payment_reminder(
        db=db,
        invoice_id=invoice_id,
        days_before_due=days_before_due
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found or already paid"
        )
    
    return {"message": "Payment reminder triggered successfully"}


@notif_router.post("/shift-confirmation/{shift_id}", status_code=status.HTTP_200_OK)
async def trigger_shift_confirmation(
    shift_id: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Trigger a shift confirmation email for an officer."""
    result = await NotificationService.trigger_shift_confirmation(
        db=db,
        shift_id=shift_id
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shift not found or not confirmed"
        )
    
    return {"message": "Shift confirmation triggered successfully"}


@notif_router.post("/payday-confirmation/{officer_id}", status_code=status.HTTP_200_OK)
async def trigger_payday_confirmation(
    officer_id: str,
    pay_date: datetime,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Trigger a payday confirmation email for an officer."""
    result = await NotificationService.trigger_payday_confirmation(
        db=db,
        officer_id=officer_id,
        pay_date=pay_date
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Officer not found"
        )
    
    return {"message": "Payday confirmation triggered successfully"}


@notif_router.post("/shift-alert/{shift_id}", status_code=status.HTTP_200_OK)
async def trigger_shift_alert(
    shift_id: str,
    hours_before: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Trigger a shift alert email for an officer."""
    result = await NotificationService.trigger_shift_alert(
        db=db,
        shift_id=shift_id,
        hours_before=hours_before
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shift not found or not confirmed"
        )
    
    return {"message": "Shift alert triggered successfully"}


@notif_router.post("/payment-received/{payment_id}", status_code=status.HTTP_200_OK)
async def trigger_payment_received(
    payment_id: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Trigger a payment received notification for a business."""
    result = await NotificationService.trigger_payment_received_for_business(
        db=db,
        payment_id=payment_id
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found or not completed"
        )
    
    return {"message": "Payment received notification triggered successfully"}


@notif_router.get("/pending", status_code=status.HTTP_200_OK)
async def get_pending_notifications(
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get pending notifications awaiting processing."""
    notifications = await NotificationService.get_pending_notifications_for_batch(
        db=db,
        limit=limit
    )
    
    return {
        "count": len(notifications),
        "limit": limit,
        "pending": [
            {
                "id": n.id,
                "recipient_email": n.recipient_email,
                "notification_type": n.notification_type,
                "subject": n.subject,
                "status": n.status,
                "scheduled_for": n.scheduled_for
            }
            for n in notifications
        ]
    }


@notif_router.post("/process-pending", status_code=status.HTTP_200_OK)
async def process_pending_notifications(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Process all pending notifications and send them."""
    results = await NotificationService.process_pending_notifications(db=db)
    
    return {
        "message": "Pending notifications processed",
        "total": results["total"],
        "sent": results["sent"],
        "failed": results["failed"],
        "errors": results["errors"]
    }
