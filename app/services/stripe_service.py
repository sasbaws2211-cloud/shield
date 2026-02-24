"""Stripe service for payment processing."""
import stripe
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import Payment, JobPosting
import logging

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.stripe_secret_key


class StripeService:
    """Stripe payment service."""

    @staticmethod
    def create_payment_intent(
        job_id: str,
        business_id: str,
        amount_gbp: float,
        description: str = None
    ) -> dict:
        """Create a Stripe payment intent for a job."""
        try:
            # Convert GBP to pence (Stripe uses smallest currency unit)
            amount_pence = int(amount_gbp * 100)

            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=amount_pence,
                currency="gbp",
                description=description or f"Payment for job {job_id}",
                metadata={
                    "job_id": job_id,
                    "business_id": business_id
                }
            )
            logger.info(f"Payment intent created: {intent.id} for job {job_id}")
            return {
                "payment_intent_id": intent.id,
                "client_secret": intent.client_secret,
                "amount_gbp": amount_gbp,
                "status": intent.status
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {e}")
            raise

    @staticmethod
    def create_payment_link(
        job_id: str,
        business_id: str,
        job_title: str,
        amount_gbp: float
    ) -> dict:
        """Create a Stripe payment link for a job posting."""
        try:
            # Convert GBP to pence (Stripe uses smallest currency unit)
            amount_pence = int(amount_gbp * 100)

            # Create payment link
            payment_link = stripe.PaymentLink.create(
                line_items=[{
                    "price_data": {
                        "currency": "gbp",
                        "product_data": {
                            "name": job_title,
                            "description": f"Security job posting - {job_title}"
                        },
                        "unit_amount": amount_pence,
                    },
                    "quantity": 1,
                }],
                metadata={
                    "job_id": job_id,
                    "business_id": business_id
                },
                after_completion={
                    "type": "redirect",
                    "redirect": {
                        "url": "https://swiftshield.com/payment/success"
                    }
                }
            )
            logger.info(f"Payment link created for job {job_id}: {payment_link.id}")
            return {
                "payment_link_id": payment_link.id,
                "payment_url": payment_link.url
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment link: {e}")
            raise

    @staticmethod
    def verify_webhook_signature(payload: str, sig_header: str) -> dict:
        """Verify Stripe webhook signature."""
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.stripe_webhook_secret
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            raise

    @staticmethod
    async def handle_payment_intent_succeeded(db: AsyncSession, event: dict) -> bool:
        """Handle payment_intent.succeeded webhook event."""
        try:
            payment_intent = event["data"]["object"]
            job_id = payment_intent.get("metadata", {}).get("job_id")
            business_id = payment_intent.get("metadata", {}).get("business_id")

            # Find payment record and update
            from app.services.payment_service import PaymentService
            result = await db.execute(
                select(Payment).where(
                    Payment.stripe_payment_intent_id == payment_intent.id
                )
            )
            payment = result.scalars().first()

            if payment:
                await PaymentService.mark_payment_complete(
                    db,
                    payment.id,
                    payment_intent.id
                )
            logger.info(f"Payment succeeded for job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Error handling payment succeeded event: {e}")
            return False

    @staticmethod
    async def handle_payment_intent_failed(db: AsyncSession, event: dict) -> bool:
        """Handle payment_intent.payment_failed webhook event."""
        try:
            payment_intent = event["data"]["object"]
            job_id = payment_intent.get("metadata", {}).get("job_id")

            # Find payment record and update
            result = await db.execute(
                select(Payment).where(
                    Payment.stripe_payment_intent_id == payment_intent.id
                )
            )
            payment = result.scalars().first()

            if payment:
                payment.status = "failed"
                payment.notes = f"Payment failed: {payment_intent.last_payment_error.message}"
                await db.commit()

            logger.error(f"Payment failed for job {job_id}: {payment_intent.last_payment_error}")
            return False
        except Exception as e:
            logger.error(f"Error handling payment failed event: {e}")
            return False

    @staticmethod
    def refund_payment(payment_intent_id: str, amount_pence: int = None) -> dict:
        """Refund a Stripe payment."""
        try:
            refund = stripe.Refund.create(
                payment_intent=payment_intent_id,
                amount=amount_pence
            )
            logger.info(f"Refund created: {refund.id} for payment intent {payment_intent_id}")
            return {
                "refund_id": refund.id,
                "amount": refund.amount,
                "status": refund.status
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error refunding payment: {e}")
            raise
