"""SQLModel ORM models for SwiftShield."""
from sqlmodel import SQLModel, Field, Relationship, Column, String, Integer, DateTime, Enum, Text
from datetime import datetime, timezone ,timedelta
from typing import Optional, List
import uuid
from decimal import Decimal 
from sqlalchemy import Column as SAColumn 
import sqlalchemy.dialects.postgresql as pg 




def now_utc():
    return datetime.now(timezone.utc)
# SIA Badge Level Enum
SIA_BADGE_LEVELS = {
    "security_guard": "Security Guard",
    "door_supervisor": "Door Supervisor",  # Main badge covering most roles
    "cctv_operator": "CCTV Operator",
    "close_protection": "Close Protection"
}


class User(SQLModel, table=True):
    """Polymorphic user table for officers, businesses, and admins."""
    __tablename__ = "users"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    role: str = Field(index=True)  # officer, business, admin
    email: str = Field(unique=True, index=True)
    password_hash: str
    status: str = Field(default="pending", index=True)  # pending, approved, rejected, active

    # Officer-only fields
    full_name: Optional[str] = None
    sia_badge_number: Optional[str] = Field(default=None, unique=True)
    badge_expiry_date: Optional[datetime] = None
    sia_badge_level: Optional[str] = None  # security_guard, door_supervisor, cctv_operator, close_protection
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    risk_level: Optional[str] = None  # low, medium, high

    # Business-only fields
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    billing_email: Optional[str] = None

    # Admin-only fields
    admin_note: Optional[str] = None

    created_at: datetime = Field(default_factory=now_utc, sa_column=SAColumn(pg.TIMESTAMP(timezone=True)))
    updated_at: datetime = Field(default_factory=now_utc, sa_column=SAColumn(pg.TIMESTAMP(timezone=True)))

    # Relationships
    officer_registrations: List["OfficerRegistration"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "OfficerRegistration.user_id"}
    )
    job_postings: List["JobPosting"] = Relationship(
        back_populates="business",
        sa_relationship_kwargs={"foreign_keys": "JobPosting.business_id"}
    )
    job_applications: List["JobApplication"] = Relationship(back_populates="officer")
    officer_shifts: List["OfficerShift"] = Relationship(back_populates="officer")
    reviewed_registrations: List["OfficerRegistration"] = Relationship(
        back_populates="reviewed_by_user",
        sa_relationship_kwargs={"foreign_keys": "OfficerRegistration.reviewed_by"}
    )
    reviewed_postings: List["JobPosting"] = Relationship(
        back_populates="reviewed_by_user",
        sa_relationship_kwargs={"foreign_keys": "JobPosting.reviewed_by"}
    )
    audit_logs: List["AuditLog"] = Relationship(back_populates="admin")
    payments: List["Payment"] = Relationship(
        back_populates="business",
        sa_relationship_kwargs={"foreign_keys": "Payment.business_id"}
    )
    invoices: List["Invoice"] = Relationship(
        back_populates="business",
        sa_relationship_kwargs={"foreign_keys": "Invoice.business_id"}
    )
    email_notifications: List["EmailNotification"] = Relationship(back_populates="recipient")


class OfficerRegistration(SQLModel, table=True):
    """Officer registration staging table."""
    __tablename__ = "officer_registrations"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    sia_badge_number: str
    badge_expiry_date: datetime
    sia_badge_level: str  # security_guard, door_supervisor, cctv_operator, close_protection
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    status: str = Field(default="pending")  # pending, approved, rejected
    risk_level: str  # low, medium, high
    reject_reason: Optional[str] = None
    reviewed_by: Optional[str] = Field(default=None, foreign_key="users.id")
    reviewed_at: Optional[datetime] = None
    submitted_at: datetime = Field(default_factory=now_utc, sa_column=SAColumn(pg.TIMESTAMP(timezone=True)))

    # Relationships
    user: Optional["User"] = Relationship(
        back_populates="officer_registrations",
        sa_relationship_kwargs={"foreign_keys": "[OfficerRegistration.user_id]"}
    )
    reviewed_by_user: Optional["User"] = Relationship(
        back_populates="reviewed_registrations",
        sa_relationship_kwargs={"foreign_keys": "[OfficerRegistration.reviewed_by]"}
    )



class JobPosting(SQLModel, table=True):
    """Job postings created by businesses."""
    __tablename__ = "job_postings"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    business_id: str = Field(foreign_key="users.id")
    title: str
    site_name: str
    site_address: Optional[str] = None
    start_time: datetime
    end_time: datetime
    guards_required: int
    required_badge_level: str = Field(default="door_supervisor")
    notes: Optional[str] = None
    budget_gbp: Optional[Decimal] = None
    status: str = Field(default="pending")  # pending, accepted, rejected
    reject_reason: Optional[str] = None
    reviewed_by: Optional[str] = Field(default=None, foreign_key="users.id")
    reviewed_at: Optional[datetime] = None
    payment_link_sent_at: Optional[datetime] = None
    stripe_payment_link_id: Optional[str] = None
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payment_method: Optional[str] = None  # stripe, bank_transfer, cash_deposit
    payment_status: str = Field(default="pending")  # pending, paid, partially_paid

    # Relationships
    business: Optional["User"] = Relationship(
        back_populates="job_postings",
        sa_relationship_kwargs={"foreign_keys": "[JobPosting.business_id]"}
    )
    reviewed_by_user: Optional["User"] = Relationship(
        back_populates="reviewed_postings",
        sa_relationship_kwargs={"foreign_keys": "[JobPosting.reviewed_by]"}
    )
    applications: List["JobApplication"] = Relationship(back_populates="job")
    shifts: List["OfficerShift"] = Relationship(back_populates="job")
    payments: List["Payment"] = Relationship(back_populates="job_posting")
    invoices: List["Invoice"] = Relationship(back_populates="job_posting")



class JobApplication(SQLModel, table=True):
    """Officer applications to job postings."""
    __tablename__ = "job_applications"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    job_id: str = Field(foreign_key="job_postings.id")
    officer_id: str = Field(foreign_key="users.id")
    status: str = Field(default="applied")  # applied, confirmed, declined
    applied_at: datetime = Field(default_factory=now_utc, sa_column=SAColumn(pg.TIMESTAMP(timezone=True)))
    updated_at: datetime = Field(default_factory=now_utc, sa_column=SAColumn(pg.TIMESTAMP(timezone=True)))

    # Relationships
    job: Optional["JobPosting"] = Relationship(back_populates="applications")
    officer: Optional["User"] = Relationship(back_populates="job_applications")
    shift: Optional["OfficerShift"] = Relationship(back_populates="application", sa_relationship_kwargs={"uselist": False})



class OfficerShift(SQLModel, table=True):
    """Officer confirmed shifts."""
    __tablename__ = "officer_shifts"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    officer_id: str = Field(foreign_key="users.id", index=True)
    job_id: str = Field(foreign_key="job_postings.id")
    application_id: str = Field(foreign_key="job_applications.id")
    title: str
    site_name: str
    start_time: datetime
    end_time: datetime
    hourly_rate_gbp: Decimal
    status: str = Field(default="confirmed")  # confirmed, cancelled
    created_at: datetime = Field(default_factory=now_utc, sa_column=SAColumn(pg.TIMESTAMP(timezone=True)))


    # Relationships
    officer: Optional["User"] = Relationship(back_populates="officer_shifts")
    job: Optional["JobPosting"] = Relationship(back_populates="shifts")
    application: Optional["JobApplication"] = Relationship(back_populates="shift")



class AuditLog(SQLModel, table=True):
    """Admin audit log for compliance."""
    __tablename__ = "audit_logs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    admin_id: str = Field(foreign_key="users.id")
    action: str
    target_id: Optional[str] = None
    target_type: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc, sa_column=SAColumn(pg.TIMESTAMP(timezone=True)))


    # Relationships
    admin: Optional["User"] = Relationship(back_populates="audit_logs")



class Payment(SQLModel, table=True):
    """Payment records for job postings with multiple payment methods."""
    __tablename__ = "payments"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    job_id: str = Field(foreign_key="job_postings.id")
    business_id: str = Field(foreign_key="users.id")
    amount_gbp: Decimal
    payment_method: str  # stripe, bank_transfer, cash_deposit
    status: str = Field(default="pending")  # pending, completed, failed, refunded
    invoice_id: Optional[str] = Field(default=None, foreign_key="invoices.id")
    stripe_payment_intent_id: Optional[str] = None
    transaction_reference: Optional[str] = None
    attempted_at: datetime = Field(default_factory=now_utc, sa_column=SAColumn(pg.TIMESTAMP(timezone=True)))

    completed_at: Optional[datetime] = None
    notes: Optional[str] = None

    # Relationships
    job_posting: Optional["JobPosting"] = Relationship(back_populates="payments")
    business: Optional["User"] = Relationship(back_populates="payments")
    invoice: Optional["Invoice"] = Relationship(back_populates="payments")



class Invoice(SQLModel, table=True):
    """Invoice records with unique numbers per payment method."""
    __tablename__ = "invoices"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    job_id: str = Field(foreign_key="job_postings.id")
    business_id: str = Field(foreign_key="users.id")
    invoice_number: str = Field(unique=True, index=True)
    payment_method: str  # stripe, bank_transfer, cash_deposit
    amount_gbp: Decimal
    status: str = Field(default="draft")  # draft, issued, paid, overdue, cancelled
    issued_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc, sa_column=SAColumn(pg.TIMESTAMP(timezone=True)))
    updated_at: datetime = Field(default_factory=now_utc, sa_column=SAColumn(pg.TIMESTAMP(timezone=True)))

    # Relationships
    job_posting: Optional["JobPosting"] = Relationship(back_populates="invoices")
    business: Optional["User"] = Relationship(back_populates="invoices")
    payments: List["Payment"] = Relationship(back_populates="invoice")



class EmailNotification(SQLModel, table=True):
    """Email notification tracking and queue."""
    __tablename__ = "email_notifications"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    recipient_email: str
    recipient_id: Optional[str] = Field(default=None, foreign_key="users.id")
    notification_type: str  # payment_reminder, shift_confirmation, payday_confirmation, shift_alert
    subject: str
    body: str
    job_id: Optional[str] = Field(default=None, foreign_key="job_postings.id")
    status: str = Field(default="pending")  # pending, sent, failed
    scheduled_for: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc, sa_column=SAColumn(pg.TIMESTAMP(timezone=True)))
   

    # Relationships
    recipient: Optional["User"] = Relationship(back_populates="email_notifications")

