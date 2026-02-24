"""Application configuration and settings."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    debug: bool = False
    environment: str 
    allowed_hosts: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Database - use async driver for PostgreSQL
    database_url: str 
    
    # JWT Authentication
    jwt_secret: str = "your-secret-key-min-256-bits-required-for-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    refresh_token_expire_days: int = 30

    # Stripe Payment Processing
    stripe_secret_key: str = ""
    stripe_public_key: str = ""
    stripe_webhook_secret: str = ""
    
    # Email - Elastic Mail configuration
    elasticmail_api_key: str = ""
    elasticmail_from_email: str = "noreply@swiftshield.com"
    elasticmail_from_name: str = "SwiftShield"

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Admin
    admin_email: str = "admin@swiftshield.com"

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 10
    rate_limit_period: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
