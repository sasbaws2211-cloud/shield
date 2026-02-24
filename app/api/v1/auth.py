"""Authentication endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.schemas.auth import (
    OfficerRegisterRequest,
    BusinessRegisterRequest,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegistrationResponse
)
from app.services.auth_service import AuthService
from app.services.email_service import EmailService

auth_router = APIRouter()


@auth_router.post("/register/officer", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_officer(
    request: OfficerRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new officer."""
    result = await AuthService.register_officer(
        db=db,
        full_name=request.full_name,
        email=request.email,
        password=request.password,
        sia_badge_number=request.sia_badge_number,
        badge_expiry_date=request.badge_expiry_date,
        sia_badge_level=request.sia_badge_level
    )
    
    # Send admin notification email (fire and forget)
    EmailService.send_admin_notification_email(
        admin_email="admin@swiftshield.com",
        subject="New Officer Registration",
        message=f"New officer registration from {request.full_name} ({request.email})"
    )
    
    return result


@auth_router.post("/register/business", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_business(
    request: BusinessRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new business."""
    result = await AuthService.register_business(
        db=db,
        company_name=request.company_name,
        contact_person=request.contact_person,
        billing_email=request.billing_email,
        email=request.email,
        password=request.password
    )
    
    # Send admin notification email (fire and forget)
    EmailService.send_admin_notification_email(
        admin_email="admin@swiftshield.com",
        subject="New Business Registration",
        message=f"New business registration from {request.company_name}"
    )
    
    return result


@auth_router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return tokens."""
    return await AuthService.login(db=db, email=request.email, password=request.password)


@auth_router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate new access token from refresh token."""
    return await AuthService.refresh_access_token(db=db, refresh_token=request.refresh_token)


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout():
    """Logout user (token invalidation handled client-side)."""
    return None
