"""Pydantic schemas for invoice-related endpoints."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from enum import Enum


class InvoiceStatusEnum(str, Enum):
    """Invoice status enumeration."""
    DRAFT = "draft"
    ISSUED = "issued"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PaymentMethodEnum(str, Enum):
    """Payment method enumeration."""
    STRIPE = "stripe"
    BANK_TRANSFER = "bank_transfer"
    CASH_DEPOSIT = "cash_deposit"


class InvoiceCreateRequest(BaseModel):
    """Create an invoice."""
    job_id: str
    business_id: str
    amount_gbp: Decimal = Field(..., ge=0.01)
    payment_method: PaymentMethodEnum
    due_at: Optional[datetime] = None
    notes: Optional[str] = None


class InvoiceResponse(BaseModel):
    """Invoice response."""
    id: str
    job_id: str
    business_id: str
    invoice_number: str
    payment_method: PaymentMethodEnum
    amount_gbp: Decimal
    status: InvoiceStatusEnum
    issued_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """List of invoices."""
    invoices: List[InvoiceResponse]
    summary: dict = Field(..., description="Total, paid, pending amounts by payment method")


class InvoiceUpdateRequest(BaseModel):
    """Update invoice details."""
    status: Optional[InvoiceStatusEnum] = None
    due_at: Optional[datetime] = None
    notes: Optional[str] = None


class InvoiceGenerationResponse(BaseModel):
    """Response for invoice generation."""
    invoice_id: str
    invoice_number: str
    status: InvoiceStatusEnum
    payment_method: PaymentMethodEnum
    amount_gbp: Decimal
    message: str
