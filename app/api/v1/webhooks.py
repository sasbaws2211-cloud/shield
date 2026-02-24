"""Webhook handlers for payment processing."""
from fastapi import APIRouter, Request, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.stripe_service import StripeService
import logging
import json

logger = logging.getLogger(__name__)

webhook_router = APIRouter()


@webhook_router.post("/stripe/payment-intent-succeeded", status_code=status.HTTP_200_OK)
async def handle_payment_intent_succeeded(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle Stripe payment_intent.succeeded webhook event."""
    try:
        # Get raw body
        body = await request.body()
        
        # Get signature header
        sig_header = request.headers.get("stripe-signature")
        if not sig_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing stripe-signature header"
            )
        
        # Verify webhook signature
        event = StripeService.verify_webhook_signature(body.decode(), sig_header)
        
        # Handle the event
        success = await StripeService.handle_payment_intent_succeeded(db, event)
        
        if not success:
            logger.warning(f"Failed to handle payment succeeded event: {event.get('id')}")
            return {"message": "Event received but processing had issues"}
        
        return {"message": "Payment success event processed"}
        
    except Exception as e:
        logger.error(f"Error handling payment intent succeeded webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook processing failed: {str(e)}"
        )


@webhook_router.post("/stripe/payment-intent-failed", status_code=status.HTTP_200_OK)
async def handle_payment_intent_failed(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle Stripe payment_intent.payment_failed webhook event."""
    try:
        # Get raw body
        body = await request.body()
        
        # Get signature header
        sig_header = request.headers.get("stripe-signature")
        if not sig_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing stripe-signature header"
            )
        
        # Verify webhook signature
        event = StripeService.verify_webhook_signature(body.decode(), sig_header)
        
        # Handle the event
        success = await StripeService.handle_payment_intent_failed(db, event)
        
        if not success:
            logger.warning(f"Failed to handle payment failed event: {event.get('id')}")
            return {"message": "Event received but processing had issues"}
        
        return {"message": "Payment failure event processed"}
        
    except Exception as e:
        logger.error(f"Error handling payment intent failed webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook processing failed: {str(e)}"
        )


@webhook_router.post("/stripe/charge-refunded", status_code=status.HTTP_200_OK)
async def handle_charge_refunded(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle Stripe charge.refunded webhook event."""
    try:
        # Get raw body
        body = await request.body()
        
        # Get signature header
        sig_header = request.headers.get("stripe-signature")
        if not sig_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing stripe-signature header"
            )
        
        # Verify webhook signature
        event = StripeService.verify_webhook_signature(body.decode(), sig_header)
        
        logger.info(f"Charge refunded event received: {event.get('id')}")
        # TODO: Implement refund handling logic
        
        return {"message": "Refund event received"}
        
    except Exception as e:
        logger.error(f"Error handling charge refunded webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook processing failed: {str(e)}"
        )


@webhook_router.post("/stripe/charge-dispute-created", status_code=status.HTTP_200_OK)
async def handle_dispute_created(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle Stripe charge.dispute.created webhook event."""
    try:
        # Get raw body
        body = await request.body()
        
        # Get signature header
        sig_header = request.headers.get("stripe-signature")
        if not sig_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing stripe-signature header"
            )
        
        # Verify webhook signature
        event = StripeService.verify_webhook_signature(body.decode(), sig_header)
        
        logger.warning(f"Dispute created event received: {event.get('id')}")
        # TODO: Implement dispute handling logic - notify admin
        
        return {"message": "Dispute event received"}
        
    except Exception as e:
        logger.error(f"Error handling dispute created webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook processing failed: {str(e)}"
        )
