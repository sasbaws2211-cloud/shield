import time
import logging
from collections import defaultdict
from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.config import settings

logger = logging.getLogger("uvicorn.access")
logger.disabled = True

request_logger = logging.getLogger("request_logger")
request_logger.setLevel(logging.INFO)


RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60

rate_limit_storage = defaultdict(list)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        rate_limit_storage[client_ip] = [
            t for t in rate_limit_storage[client_ip] 
            if current_time - t < RATE_LIMIT_WINDOW
        ]
        
        if len(rate_limit_storage[client_ip]) >= RATE_LIMIT_REQUESTS:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."}
            )
        
        rate_limit_storage[client_ip].append(current_time)
        
        response = await call_next(request)
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        if request.url.path.startswith("/api"):
            request_logger.info(
                f"{request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Duration: {process_time:.3f}s"
            )
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        
        return response


def register_middleware(app: FastAPI):
    app.add_middleware(SecurityHeadersMiddleware)
    
    app.add_middleware(RequestLoggingMiddleware)
    
    app.add_middleware(RateLimitMiddleware)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts,
    )
