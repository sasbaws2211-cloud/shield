"""Pydantic schemas for payment-related endpoints."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict
from decimal import Decimal
from enum import Enum


class PaymentMethodEnum(str, Enum):
    """Payment method enumeration."""
    STRIPE = "stripe"
    BANK_TRANSFER = "bank_transfer"
    CASH_DEPOSIT = "cash_deposit"


class PaymentStatusEnum(str, Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentSelectionRequest(BaseModel):
    """Request to select payment method for a job."""
    job_id: str
    payment_method: PaymentMethodEnum = Field(..., description="Selected payment method")


class PaymentCreateRequest(BaseModel):
    """Create a payment record."""
    job_id: str
    amount_gbp: Decimal = Field(..., ge=0.01)
    payment_method: PaymentMethodEnum
    transaction_reference: Optional[str] = Field(None, description="For bank transfer or cash deposits")


class PaymentResponse(BaseModel):
    """Payment response."""
    id: str
    job_id: str
    business_id: str
    amount_gbp: Decimal
    payment_method: PaymentMethodEnum
    status: PaymentStatusEnum
    invoice_id: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None
    transaction_reference: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentFailureResponse(BaseModel):
    """Payment failure response."""
    error: str
    message: str
    payment_id: Optional[str] = None
    job_id: str
    suggested_action: Optional[str] = None


class PaymentMethodCheckResponse(BaseModel):
    """Response for checking if Stripe is required."""
    is_stripe_required: bool
    hours_until_start: float
    payment_method_allowed: list[PaymentMethodEnum]
    message: str


class PaymentSummaryResponse(BaseModel):
    """Payment summary for a business."""
    business_id: str
    total_gbp: Decimal
    by_method: Dict[str, Decimal]
    pending_gbp: Decimal
    completed_gbp: Decimal


class InvoiceResponse(BaseModel):
    """Invoice response."""
    id: str
    job_id: str
    invoice_number: str
    amount_gbp: Decimal
    payment_method: PaymentMethodEnum
    status: str
    issued_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None

    class Config:
        from_attributes = True
