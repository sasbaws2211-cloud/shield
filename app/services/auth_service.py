"""Authentication service with business logic."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from app.models.models import User, OfficerRegistration
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.core.config import settings
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service with async database operations."""

    @staticmethod
    def calculate_risk_level(badge_expiry_date: datetime) -> str:
        """Calculate risk level based on badge expiry date."""
        days_until_expiry = (badge_expiry_date.date() - datetime.now(timezone.utc).date()).days
        if days_until_expiry > 180:
            return "low"
        elif days_until_expiry >= 60:
            return "medium"
        else:
            return "high"

    @staticmethod
    async def register_officer(
        db: AsyncSession,
        full_name: str,
        email: str,
        password: str,
        sia_badge_number: str,
        badge_expiry_date: datetime,
        sia_badge_level: str,
        emergency_contact_name: str = None,
        emergency_contact_phone: str = None,
        emergency_contact_relationship: str = None
    ) -> dict:
        """Register a new officer with SIA badge level and emergency contact."""
        # Check if email already exists
        result = await db.execute(select(User).where(User.email == email))
        existing_user = result.scalars().first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Check if SIA badge already exists (unique constraint)
        result = await db.execute(select(User).where(User.sia_badge_number == sia_badge_number))
        existing_badge = result.scalars().first()
        
        if existing_badge:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SIA badge number already registered. If lost and replaced, contact admin to update."
            )

        # Validate badge level is valid
        valid_levels = ["security_guard", "door_supervisor", "cctv_operator", "close_protection"]
        if sia_badge_level not in valid_levels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid badge level. Must be one of: {', '.join(valid_levels)}"
            )

        # Validate emergency contact if provided
        if emergency_contact_name and not (emergency_contact_phone and emergency_contact_relationship):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="If emergency contact name is provided, phone and relationship are required"
            )

        # Calculate risk level
        risk_level = AuthService.calculate_risk_level(badge_expiry_date)

        # Create user
        user = User(
            role="officer",
            email=email,
            password_hash=hash_password(password),
            status="pending",
            full_name=full_name,
            sia_badge_number=sia_badge_number,
            badge_expiry_date=badge_expiry_date,
            sia_badge_level=sia_badge_level,
            emergency_contact_name=emergency_contact_name,
            emergency_contact_phone=emergency_contact_phone,
            emergency_contact_relationship=emergency_contact_relationship,
            risk_level=risk_level
        )
        db.add(user)
        await db.flush()

        # Create officer registration record
        registration = OfficerRegistration(
            user_id=user.id,
            sia_badge_number=sia_badge_number,
            badge_expiry_date=badge_expiry_date,
            sia_badge_level=sia_badge_level,
            emergency_contact_name=emergency_contact_name,
            emergency_contact_phone=emergency_contact_phone,
            emergency_contact_relationship=emergency_contact_relationship,
            status="pending",
            risk_level=risk_level
        )
        db.add(registration)
        await db.commit()
        logger.info(f"Officer registered: {email} with badge level: {sia_badge_level}")
        return {
            "message": "Registration submitted. Your SIA badge will be verified within 24 hours.",
            "registration_id": registration.id
        }

    @staticmethod
    async def register_business(
        db: AsyncSession,
        company_name: str,
        contact_person: str,
        billing_email: str,
        email: str,
        password: str
    ) -> dict:
        """Register a new business."""
        # Check if email already exists
        result = await db.execute(select(User).where(User.email == email))
        existing_user = result.scalars().first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create user
        user = User(
            role="business",
            email=email,
            password_hash=hash_password(password),
            status="pending",
            company_name=company_name,
            contact_person=contact_person,
            billing_email=billing_email
        )
        db.add(user)
        await db.commit()
        logger.info(f"Business registered: {email}")
        return {
            "message": "Account pending admin approval. You will be notified by email.",
            "user_id": user.id
        }

    @staticmethod
    async def login(db: AsyncSession, email: str, password: str) -> dict:
        """Authenticate user and return tokens."""
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Check if user is approved
        if user.status not in ["approved", "active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account status is {user.status}"
            )

        # Create tokens
        token_data = {
            "sub": user.id,
            "role": user.role,
            "email": user.email
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        logger.info(f"User logged in: {email}")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "role": user.role,
                "email": user.email,
                "status": user.status,
                "full_name": user.full_name,
                "sia_badge_number": user.sia_badge_number,
                "sia_badge_level": user.sia_badge_level,
                "badge_expiry_date": user.badge_expiry_date,
                "company_name": user.company_name,
                "contact_person": user.contact_person
            }
        }

    @staticmethod
    async def refresh_access_token(db: AsyncSession, refresh_token: str) -> dict:
        """Generate new access token from refresh token."""
        from app.core.security import decode_token
        payload = decode_token(refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        user_id = payload.get("sub")
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        token_data = {
            "sub": user.id,
            "role": user.role,
            "email": user.email
        }
        access_token = create_access_token(token_data)
        logger.info(f"Access token refreshed for user: {user.email}")
        return {
            "access_token": access_token,
            "user": {
                "id": user.id,
                "role": user.role,
                "email": user.email,
                "status": user.status
            }
        }

            
