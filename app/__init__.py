"V1 API router initialization."
from fastapi import FastAPI
from middleware import register_middleware
from app.api.v1.jobs import jobs_router
from app.api.v1.admin import admin_router
from app.api.v1.payments import pay_router
from app.api.v1.notifications import notif_router
from app.api.v1.webhooks import webhook_router
from app.api.v1.auth import auth_router

version = "v1"

description = """
A REST API for a Fintech Application Service.
    """

version_prefix =f"/api/{version}"

app = FastAPI( 
    title="SwiftShield",
    description=description,
    version=version,
    license_info={"name": "MIT License", "url": "https://opensource.org/license/mit"},
    contact={
        "url": "https://github.com/sasbaws221",
        "email": "ssako@faabsystems.com",
    },
    terms_of_service="https://example.com/tos",
    openapi_url=f"{version_prefix}/openapi.json",
    docs_url=f"{version_prefix}/docs",
    redoc_url=f"{version_prefix}/redoc"
)

register_middleware(app)
# Include routers 
app.include_router(auth_router, prefix=f"{version_prefix}", tags=["Auth"]) 
app.include_router(admin_router, prefix=f"{version_prefix}", tags=["Admin"]) 
app.include_router(pay_router, prefix=f"{version_prefix}", tags=["Payment"]) 
app.include_router(notif_router, prefix=f"{version_prefix}", tags=["Notifications"]) 
app.include_router(webhook_router, prefix=f"{version_prefix}", tags=["Webhook"]) 
app.include_router(jobs_router, prefix=f"{version_prefix}", tags=["Jobs"])
